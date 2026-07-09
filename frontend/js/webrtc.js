/**
 * WebRTC peer connection manager.
 *
 * Two modes:
 *  - Teacher:  sends camera + audio → all connected peers receive it.
 *  - Student:  sends nothing → receives teacher's stream only.
 *              Uses recvonly transceivers so SDP negotiation works correctly.
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
        } catch (e) {
            console.warn("Camera/mic access denied:", e.message);
            this.localStream = new MediaStream();
        }
        return this.localStream;
    }

    // ── Peer management ───────────────────────────────────

    async createPeer(remotePeerId, isInitiator) {
        // Don't create duplicate connections
        if (this.peers[remotePeerId]) return this.peers[remotePeerId];

        const pc = new RTCPeerConnection({
            iceServers: this.stunServers || [{ urls: "stun:stun.l.google.com:19302" }],
        });

        if (this.userRole === "teacher") {
            // Teacher: add real camera + audio tracks so students can receive them
            if (this.localStream) {
                this.localStream.getTracks().forEach(track => pc.addTrack(track, this.localStream));
            }
        } else {
            // Student: add recvonly transceivers — no camera sent, but can receive teacher video
            pc.addTransceiver("video", { direction: "recvonly" });
            pc.addTransceiver("audio", { direction: "recvonly" });
        }

        // Receive remote stream
        pc.ontrack = (event) => {
            const remoteStream = event.streams[0] || new MediaStream([event.track]);
            console.log("[WebRTC] ontrack fired for", remotePeerId, event.track.kind);
            this.onStreamAdded(remotePeerId, remoteStream);
        };

        // Send ICE candidates via signaling
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                this.ws.send(JSON.stringify({
                    type: "webrtc_ice",
                    target: remotePeerId,
                    payload: { candidate: event.candidate, target: remotePeerId },
                }));
            }
        };

        pc.onconnectionstatechange = () => {
            console.log("[WebRTC] connection state →", pc.connectionState, "peer:", remotePeerId);
            if (["disconnected", "failed", "closed"].includes(pc.connectionState)) {
                this.removePeer(remotePeerId);
                this.onStreamRemoved(remotePeerId);
            }
        };

        this.peers[remotePeerId] = pc;

        if (isInitiator) {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            this.ws.send(JSON.stringify({
                type: "webrtc_offer",
                target: remotePeerId,
                payload: { sdp: pc.localDescription, target: remotePeerId },
            }));
        }

        return pc;
    }

    async handleOffer(fromPeerId, sdp) {
        const pc = await this.createPeer(fromPeerId, false);
        await pc.setRemoteDescription(new RTCSessionDescription(sdp));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        this.ws.send(JSON.stringify({
            type: "webrtc_answer",
            target: fromPeerId,
            payload: { sdp: pc.localDescription, target: fromPeerId },
        }));
    }

    async handleAnswer(fromPeerId, sdp) {
        const pc = this.peers[fromPeerId];
        if (pc) await pc.setRemoteDescription(new RTCSessionDescription(sdp));
    }

    async handleIce(fromPeerId, candidate) {
        const pc = this.peers[fromPeerId];
        if (pc) {
            try { await pc.addIceCandidate(new RTCIceCandidate(candidate)); }
            catch (e) { console.warn("ICE error:", e); }
        }
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
            return false;
        }
        try {
            this.screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
            const screenTrack = this.screenStream.getVideoTracks()[0];
            Object.values(this.peers).forEach(pc => {
                const sender = pc.getSenders().find(s => s.track?.kind === "video");
                if (sender) sender.replaceTrack(screenTrack);
            });
            screenTrack.onended = () => this.toggleScreenShare();
            return true;
        } catch (e) {
            console.warn("Screen share cancelled:", e);
            return false;
        }
    }
}