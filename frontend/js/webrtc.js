/**
 * WebRTC peer connection manager.
 *
 * Architecture:
 *  - Teacher:  ALWAYS the initiator. Adds camera + audio tracks, creates offer.
 *  - Student:  ALWAYS the answerer. Never adds tracks, never initiates.
 *              Browser auto-creates recvonly transceivers from the teacher's offer SDP.
 *              ontrack fires when teacher's video/audio arrives.
 *
 * Key rule: DO NOT pre-add transceivers when answering — it breaks SDP negotiation.
 */
class WebRTCManager {
    constructor(ws, stunServers, onStreamAdded, onStreamRemoved) {
        this.ws = ws;
        this.stunServers = stunServers;
        this.onStreamAdded = onStreamAdded;
        this.onStreamRemoved = onStreamRemoved;
        this.peers = {};           // peer_id → RTCPeerConnection
        this.localStream = null;
        this.myPeerId = null;
        this.userRole = "student"; // set by classroom.html after init
        this.micMuted = false;
        this.camOff = false;
        this.screenStream = null;
        this.pendingCandidates = {};  // peer_id → [RTCIceCandidate, ...] queued before remoteDesc
    }

    // ── Local media ───────────────────────────────────────

    async startLocalMedia(videoEl) {
        try {
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 1920 }, height: { ideal: 1080 }, facingMode: "user" },
                audio: { echoCancellation: true, noiseSuppression: true },
            });
            videoEl.srcObject = this.localStream;
            videoEl.muted = true;   // don't echo yourself
            console.log("[WebRTC] Local media started:", this.localStream.getTracks().length, "tracks");
        } catch (e) {
            console.warn("[WebRTC] Camera/mic access denied:", e.message);
            this.localStream = new MediaStream();
        }
        return this.localStream;
    }

    // ── Peer management ───────────────────────────────────

    _buildPeerConnection(remotePeerId) {
        const pc = new RTCPeerConnection({
            iceServers: [
                // STUN servers (for same-network / simple NAT)
                { urls: "stun:stun.l.google.com:19302" },
                { urls: "stun:stun1.l.google.com:19302" },
                { urls: "stun:stun2.l.google.com:19302" },
                // Free open TURN relay (Metered open relay — required for cross-network video)
                {
                    urls: "turn:openrelay.metered.ca:80",
                    username: "openrelayproject",
                    credential: "openrelayproject",
                },
                {
                    urls: "turn:openrelay.metered.ca:443",
                    username: "openrelayproject",
                    credential: "openrelayproject",
                },
                {
                    urls: "turn:openrelay.metered.ca:443?transport=tcp",
                    username: "openrelayproject",
                    credential: "openrelayproject",
                },
                {
                    urls: "turns:openrelay.metered.ca:443",
                    username: "openrelayproject",
                    credential: "openrelayproject",
                },
            ],
            iceCandidatePoolSize: 10,
        });

        // ── ontrack: receive remote stream ──
        // Called once per track. Use the stream from event.streams[0] if available.
        const pendingTracks = [];
        pc.ontrack = (event) => {
            console.log("[WebRTC] ontrack:", event.track.kind, "from", remotePeerId);
            if (event.streams && event.streams[0]) {
                // Use the fully assembled stream directly
                this.onStreamAdded(remotePeerId, event.streams[0]);
            } else {
                // Fallback: collect tracks and assemble a stream
                pendingTracks.push(event.track);
                const stream = new MediaStream(pendingTracks);
                this.onStreamAdded(remotePeerId, stream);
            }
        };

        // ── ICE candidates ──
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                this.ws.send(JSON.stringify({
                    type: "webrtc_ice",
                    target: remotePeerId,
                    payload: { candidate: event.candidate, target: remotePeerId },
                }));
            }
        };

        pc.oniceconnectionstatechange = () => {
            console.log("[WebRTC] ICE state →", pc.iceConnectionState, "peer:", remotePeerId);
        };

        pc.onconnectionstatechange = () => {
            console.log("[WebRTC] Connection →", pc.connectionState, "peer:", remotePeerId);
            if (["disconnected", "failed", "closed"].includes(pc.connectionState)) {
                this.removePeer(remotePeerId);
                this.onStreamRemoved(remotePeerId);
            }
        };

        return pc;
    }

    async createPeer(remotePeerId, isInitiator) {
        // Don't create duplicate connections
        if (this.peers[remotePeerId]) {
            console.log("[WebRTC] Peer already exists for", remotePeerId);
            return this.peers[remotePeerId];
        }

        console.log("[WebRTC] createPeer", remotePeerId, "initiator:", isInitiator, "role:", this.userRole);
        const pc = this._buildPeerConnection(remotePeerId);

        // ======================================================
        // ZOOM-STYLE WEBRTC
        // CAMERA FULL PANEL -> SCREEN FULL PANEL -> CAMERA RETURN
        // ======================================================

        if (this.userRole === "teacher") {

            if (!this.localStream) {
                console.error("[WebRTC] Teacher local stream missing");
                return pc;
            }

            // --------------------------------------------------
            // AUDIO
            // --------------------------------------------------

            const audioTrack = this.localStream.getAudioTracks()[0];

            if (audioTrack) {
                pc.addTrack(audioTrack, this.localStream);
            }

            // --------------------------------------------------
            // CAMERA
            // Camera keeps running in background
            // --------------------------------------------------

            const cameraTrack = this.localStream.getVideoTracks()[0];

            if (cameraTrack) {

                const videoSender = pc.addTrack(
                    cameraTrack,
                    this.localStream
                );

                pc._teacherVideoSender = videoSender;

                console.log("[WebRTC] Teacher camera added");
            }

        } else {

            // --------------------------------------------------
            // STUDENT RECEIVE TEACHER
            // --------------------------------------------------

            pc.addTransceiver("video", {
                direction: "recvonly"
            });

            pc.addTransceiver("audio", {
                direction: "recvonly"
            });

            const teacherStream = new MediaStream();

            pc.ontrack = (event) => {

                if (
                    !teacherStream
                        .getTracks()
                        .some(track => track.id === event.track.id)
                ) {
                    teacherStream.addTrack(event.track);
                }

                let video = document.getElementById("teacherVideo");

                if (!video) {

                    video = document.createElement("video");

                    video.id = "teacherVideo";
                    video.autoplay = true;
                    video.playsInline = true;

                    const panel =
                        document.getElementById("video-grid") ||
                        document.querySelector(".video-grid") ||
                        document.querySelector(".video-panel") ||
                        document.getElementById("videoGrid");

                    if (panel) {
                        panel.innerHTML = "";
                        panel.appendChild(video);
                    }
                }

                video.srcObject = teacherStream;

                video.style.width = "100%";
                video.style.height = "100%";
                video.style.objectFit = "cover";
                video.style.objectPosition = "center";
                video.style.background = "#000";

                video.play().catch(console.warn);
            };
        }

        // ------------------------------------------------------
        // STORE PEER
        // ------------------------------------------------------

        this.peers[remotePeerId] = pc;


        // ======================================================
        // START SCREEN SHARE
        // ======================================================

        // Bind to toggleScreenShare so the HTML button triggers this logic
        this.toggleScreenShare = async () => {

            if (this.userRole !== "teacher") return;

            // If already sharing, we rely on the native "Stop Sharing" button which triggers onended,
            // but if they click the HTML button again, let's stop it properly to toggle it off.
            if (this.screenStream) {
                this.screenStream.getTracks().forEach(t => t.stop());
                const videoTrack = this.screenStream.getVideoTracks()[0];
                if (videoTrack && videoTrack.onended) videoTrack.onended();
                return false;
            }

            try {

                this.screenStream =
                    await navigator.mediaDevices.getDisplayMedia({
                        video: true,
                        audio: false
                    });

                const screenTrack =
                    this.screenStream.getVideoTracks()[0];

                if (!screenTrack) return false;

                console.log("[WebRTC] SCREEN SHARE STARTED");

                // Replace camera with screen for EVERY student

                for (const peerId in this.peers) {

                    const peer = this.peers[peerId];

                    const sender =
                        peer._teacherVideoSender ||
                        peer.getSenders().find(
                            sender => sender.track?.kind === "video"
                        );

                    if (sender) {
                        await sender.replaceTrack(screenTrack);
                    }
                }

                // Screen fills full panel

                const localVideo =
                    document.getElementById("video-local") ||
                    document.getElementById("teacherVideo") ||
                    document.getElementById("localVideo");

                if (localVideo) {

                    localVideo.srcObject = this.screenStream;

                    localVideo.style.width = "100%";
                    localVideo.style.height = "100%";
                    localVideo.style.objectFit = "contain";
                    localVideo.style.objectPosition = "center";
                    localVideo.style.background = "#000";
                }

                // Camera is NOT stopped.
                // Camera continues running in localStream.

                screenTrack.onended = async () => {

                    console.log("[WebRTC] SCREEN SHARE STOPPED");

                    const cameraTrack =
                        this.localStream
                            ?.getVideoTracks()[0];

                    if (!cameraTrack) return;

                    // Return camera to EVERY student

                    for (const peerId in this.peers) {

                        const peer = this.peers[peerId];

                        const sender =
                            peer._teacherVideoSender ||
                            peer.getSenders().find(
                                sender => sender.track?.kind === "video"
                            );

                        if (sender) {
                            await sender.replaceTrack(cameraTrack);
                        }
                    }

                    // Return teacher panel to camera

                    if (localVideo) {

                        localVideo.srcObject = this.localStream;

                        localVideo.style.width = "100%";
                        localVideo.style.height = "100%";
                        localVideo.style.objectFit = "cover";
                        localVideo.style.objectPosition = "center";
                    }

                    this.screenStream = null;

                    const btn = document.getElementById("btn-screen");
                    if (btn) btn.classList.remove("active");

                    console.log(
                        "[WebRTC] CAMERA RESTORED"
                    );
                };

                return true;

            } catch (error) {

                console.error(
                    "[WebRTC] Screen share error:",
                    error
                );
                return false;
            }
        };


        // ======================================================
        // FULL VIDEO PANEL CSS
        // ======================================================

        if (!document.getElementById("webrtc-video-style")) {

            const style = document.createElement("style");

            style.id = "webrtc-video-style";

            style.textContent = `
                #videoGrid,
                #video-grid,
                .video-grid,
                .video-panel {
                    width: 100% !important;
                    height: 100% !important;
                    min-height: 0 !important;
                    overflow: hidden !important;
                    background: #000 !important;
                }

                #teacherVideo,
                #localVideo,
                #video-local {
                    width: 100% !important;
                    height: 100% !important;
                    max-width: none !important;
                    max-height: none !important;
                    display: block !important;
                    object-fit: cover;
                    object-position: center;
                    background: #000;
                }
            `;

            document.head.appendChild(style);
        }

        if (isInitiator) {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            console.log("[WebRTC] Sending offer to", remotePeerId);
            this.ws.send(JSON.stringify({
                type: "webrtc_offer",
                target: remotePeerId,
                payload: { sdp: pc.localDescription, target: remotePeerId },
            }));
        }

        return pc;
    }

    async handleOffer(fromPeerId, sdp) {
        console.log("[WebRTC] Handling offer from", fromPeerId);
        // Create a peer WITHOUT pre-adding any tracks or transceivers.
        // setRemoteDescription will set up the right transceivers from the SDP.
        const pc = await this.createPeer(fromPeerId, false);
        await pc.setRemoteDescription(new RTCSessionDescription(sdp));
        await this._flushPendingCandidates(fromPeerId);  // flush any early ICE candidates
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        console.log("[WebRTC] Sending answer to", fromPeerId);
        this.ws.send(JSON.stringify({
            type: "webrtc_answer",
            target: fromPeerId,
            payload: { sdp: pc.localDescription, target: fromPeerId },
        }));
    }

    async handleAnswer(fromPeerId, sdp) {
        const pc = this.peers[fromPeerId];
        if (pc) {
            console.log("[WebRTC] Handling answer from", fromPeerId);
            await pc.setRemoteDescription(new RTCSessionDescription(sdp));
            await this._flushPendingCandidates(fromPeerId);
        }
    }

    async handleIce(fromPeerId, candidate) {
        const pc = this.peers[fromPeerId];
        if (!pc) return;
        // If remote description isn't set yet, queue the candidate
        if (!pc.remoteDescription) {
            if (!this.pendingCandidates[fromPeerId]) this.pendingCandidates[fromPeerId] = [];
            this.pendingCandidates[fromPeerId].push(candidate);
            console.log("[WebRTC] Queued ICE candidate for", fromPeerId);
            return;
        }
        try { await pc.addIceCandidate(new RTCIceCandidate(candidate)); }
        catch (e) { console.warn("[WebRTC] ICE error:", e); }
    }

    async _flushPendingCandidates(fromPeerId) {
        const candidates = this.pendingCandidates[fromPeerId] || [];
        delete this.pendingCandidates[fromPeerId];
        const pc = this.peers[fromPeerId];
        for (const c of candidates) {
            try { await pc.addIceCandidate(new RTCIceCandidate(c)); }
            catch (e) { console.warn("[WebRTC] Flushed ICE error:", e); }
        }
        if (candidates.length) console.log("[WebRTC] Flushed", candidates.length, "queued ICE candidates for", fromPeerId);
    }

    removePeer(peerId) {
        const pc = this.peers[peerId];
        if (pc) { pc.close(); delete this.peers[peerId]; }
    }

    disconnectAll() {
        Object.keys(this.peers).forEach(id => this.removePeer(id));
        if (this.localStream) this.localStream.getTracks().forEach(t => t.stop());
        if (this.screenStream) this.screenStream.getTracks().forEach(t => t.stop());
    }

    // ── Media controls ────────────────────────────────────

    toggleMic() {
        this.micMuted = !this.micMuted;
        this.localStream?.getAudioTracks().forEach(t => t.enabled = !this.micMuted);
        return this.micMuted;
    }

    toggleCam() {
        this.camOff = !this.camOff;
        this.localStream?.getVideoTracks().forEach(t => t.enabled = !this.camOff);
        return this.camOff;
    }

    async toggleScreenShare() {
        const localVideo = document.getElementById("video-local");
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(t => t.stop());
            this.screenStream = null;
            const camTrack = this.localStream?.getVideoTracks()[0];
            if (camTrack) {
                Object.values(this.peers).forEach(pc => {
                    const sender = pc.getSenders().find(s => s.track?.kind === "video");
                    if (sender) sender.replaceTrack(camTrack);
                });
            }
            if (localVideo && this.localStream) {
                localVideo.srcObject = this.localStream;
            }
            return false;
        }
        try {
            this.screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
            const screenTrack = this.screenStream.getVideoTracks()[0];
            Object.values(this.peers).forEach(pc => {
                const sender = pc.getSenders().find(s => s.track?.kind === "video");
                if (sender) sender.replaceTrack(screenTrack);
            });
            if (localVideo) {
                localVideo.srcObject = this.screenStream;
            }
            screenTrack.onended = () => {
                this.toggleScreenShare();
                const btn = document.getElementById("btn-screen");
                if (btn) btn.classList.remove("active");
            };
            return true;
        } catch (e) {
            console.warn("[WebRTC] Screen share cancelled:", e);
            return false;
        }
    }
}