class WebRTCManager {
    constructor(ws, stunServers, onStreamAdded, onStreamRemoved) {
        this.ws = ws;
        this.stunServers = stunServers;
        this.onStreamAdded = onStreamAdded;
        this.onStreamRemoved = onStreamRemoved;

        this.peers = {};
        this.localStream = null;
        this.myPeerId = null;
        this.userRole = "student";

        this.micMuted = false;
        this.camOff = false;
        this.screenStream = null;

        this.pendingCandidates = {};
    }

    // =====================================================
    // LOCAL CAMERA + MICROPHONE
    // =====================================================

    async startLocalMedia(videoEl) {
        try {
            this.localStream =
                await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: { ideal: 1920 },
                        height: { ideal: 1080 },
                        facingMode: "user"
                    },
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true
                    }
                });

            if (videoEl) {
                videoEl.srcObject = this.localStream;
                videoEl.autoplay = true;
                videoEl.playsInline = true;
                videoEl.muted = true;

                videoEl.style.width = "100%";
                videoEl.style.height = "100%";
                videoEl.style.objectFit = "cover";
                videoEl.style.objectPosition = "center";
            }

            console.log("[WebRTC] Local media started");

        } catch (error) {
            console.error("[WebRTC] Media error:", error);

            this.localStream = new MediaStream();
        }

        return this.localStream;
    }


    // =====================================================
    // BUILD PEER CONNECTION
    // =====================================================

    _buildPeerConnection(remotePeerId) {

        const pc = new RTCPeerConnection({
            iceServers: [
                {
                    urls: "stun:stun.l.google.com:19302"
                },
                {
                    urls: "stun:stun1.l.google.com:19302"
                },
                {
                    urls: "stun:stun2.l.google.com:19302"
                },
                {
                    urls: "turn:openrelay.metered.ca:80",
                    username: "openrelayproject",
                    credential: "openrelayproject"
                },
                {
                    urls: "turn:openrelay.metered.ca:443",
                    username: "openrelayproject",
                    credential: "openrelayproject"
                },
                {
                    urls: "turn:openrelay.metered.ca:443?transport=tcp",
                    username: "openrelayproject",
                    credential: "openrelayproject"
                },
                {
                    urls: "turns:openrelay.metered.ca:443",
                    username: "openrelayproject",
                    credential: "openrelayproject"
                }
            ],

            iceCandidatePoolSize: 10
        });


        // =================================================
        // STUDENT RECEIVES TEACHER STREAM
        // =================================================

        const remoteStream = new MediaStream();

        pc.ontrack = async (event) => {

            console.log(
                "[WebRTC] Track received:",
                event.track.kind,
                remotePeerId
            );

            if (
                !remoteStream
                    .getTracks()
                    .some(track => track.id === event.track.id)
            ) {
                remoteStream.addTrack(event.track);
            }

            this.onStreamAdded(
                remotePeerId,
                remoteStream
            );
        };


        // =================================================
        // ICE
        // =================================================

        pc.onicecandidate = event => {

            if (!event.candidate) return;

            this.ws.send(JSON.stringify({
                type: "webrtc_ice",

                target: remotePeerId,

                payload: {
                    candidate: event.candidate,
                    target: remotePeerId
                }
            }));
        };


        pc.oniceconnectionstatechange = () => {

            console.log(
                "[WebRTC] ICE:",
                pc.iceConnectionState,
                remotePeerId
            );
        };


        pc.onconnectionstatechange = () => {

            console.log(
                "[WebRTC] Connection:",
                pc.connectionState,
                remotePeerId
            );

            if (
                pc.connectionState === "failed" ||
                pc.connectionState === "closed"
            ) {
                this.removePeer(remotePeerId);

                this.onStreamRemoved(remotePeerId);
            }
        };


        return pc;
    }


    // =====================================================
    // CREATE PEER
    // TEACHER ALWAYS SENDS CAMERA/AUDIO
    // STUDENT ONLY RECEIVES
    // =====================================================

    async createPeer(remotePeerId, isInitiator) {

        if (this.peers[remotePeerId]) {
            return this.peers[remotePeerId];
        }

        const pc =
            this._buildPeerConnection(remotePeerId);


        // =================================================
        // TEACHER
        // =================================================

        if (this.userRole === "teacher") {

            if (!this.localStream) {
                console.error(
                    "[WebRTC] Teacher stream missing"
                );

                return pc;
            }


            // AUDIO

            const audioTrack =
                this.localStream.getAudioTracks()[0];

            if (audioTrack) {

                pc.addTrack(
                    audioTrack,
                    this.localStream
                );
            }


            // VIDEO

            const cameraTrack =
                this.localStream.getVideoTracks()[0];

            if (cameraTrack) {

                const sender = pc.addTrack(
                    cameraTrack,
                    this.localStream
                );

                pc._teacherVideoSender = sender;
            }
        }


        // IMPORTANT:
        // STUDENT DOES NOT addTrack()
        // STUDENT DOES NOT addTransceiver()
        // Teacher offer automatically creates receivers.


        this.peers[remotePeerId] = pc;


        // =================================================
        // TEACHER CREATES OFFER
        // =================================================

        if (isInitiator) {

            const offer =
                await pc.createOffer();

            await pc.setLocalDescription(offer);


            this.ws.send(JSON.stringify({
                type: "webrtc_offer",

                target: remotePeerId,

                payload: {
                    sdp: pc.localDescription,
                    target: remotePeerId
                }
            }));


            console.log(
                "[WebRTC] Offer sent:",
                remotePeerId
            );
        }


        return pc;
    }


    // =====================================================
    // HANDLE OFFER
    // =====================================================

    async handleOffer(fromPeerId, sdp) {

        console.log(
            "[WebRTC] Offer received:",
            fromPeerId
        );


        const pc =
            await this.createPeer(
                fromPeerId,
                false
            );


        await pc.setRemoteDescription(
            new RTCSessionDescription(sdp)
        );


        await this._flushPendingCandidates(
            fromPeerId
        );


        const answer =
            await pc.createAnswer();


        await pc.setLocalDescription(answer);


        this.ws.send(JSON.stringify({
            type: "webrtc_answer",

            target: fromPeerId,

            payload: {
                sdp: pc.localDescription,
                target: fromPeerId
            }
        }));


        console.log(
            "[WebRTC] Answer sent:",
            fromPeerId
        );
    }


    // =====================================================
    // HANDLE ANSWER
    // =====================================================

    async handleAnswer(fromPeerId, sdp) {

        const pc =
            this.peers[fromPeerId];


        if (!pc) return;


        await pc.setRemoteDescription(
            new RTCSessionDescription(sdp)
        );


        await this._flushPendingCandidates(
            fromPeerId
        );
    }


    // =====================================================
    // HANDLE ICE
    // =====================================================

    async handleIce(fromPeerId, candidate) {

        const pc =
            this.peers[fromPeerId];


        if (!pc) return;


        if (!pc.remoteDescription) {

            if (!this.pendingCandidates[fromPeerId]) {
                this.pendingCandidates[fromPeerId] = [];
            }


            this.pendingCandidates[fromPeerId]
                .push(candidate);


            return;
        }


        try {

            await pc.addIceCandidate(
                new RTCIceCandidate(candidate)
            );

        } catch (error) {

            console.warn(
                "[WebRTC] ICE error:",
                error
            );
        }
    }


    async _flushPendingCandidates(peerId) {

        const pc =
            this.peers[peerId];


        if (!pc) return;


        const candidates =
            this.pendingCandidates[peerId] || [];


        delete this.pendingCandidates[peerId];


        for (const candidate of candidates) {

            try {

                await pc.addIceCandidate(
                    new RTCIceCandidate(candidate)
                );

            } catch (error) {

                console.warn(
                    "[WebRTC] ICE flush error:",
                    error
                );
            }
        }
    }


    // =====================================================
    // ZOOM STYLE SCREEN SHARE
    // SCREEN FULL PANEL
    // CAMERA CONTINUES IN BACKGROUND
    // =====================================================

    async toggleScreenShare() {

        if (this.userRole !== "teacher") {
            return false;
        }


        const localVideo =
            document.getElementById("video-local") ||
            document.getElementById("localVideo");


        // =================================================
        // STOP SCREEN SHARE
        // =================================================

        if (this.screenStream) {

            const oldScreenStream =
                this.screenStream;


            this.screenStream = null;


            oldScreenStream
                .getTracks()
                .forEach(track => track.stop());


            await this._restoreCamera(localVideo);


            return false;
        }


        // =================================================
        // START SCREEN SHARE
        // =================================================

        try {

            this.screenStream =
                await navigator.mediaDevices
                    .getDisplayMedia({
                        video: true,
                        audio: false
                    });


            const screenTrack =
                this.screenStream
                    .getVideoTracks()[0];


            if (!screenTrack) {

                this.screenStream = null;

                return false;
            }


            // SEND SCREEN TO EVERY STUDENT

            for (
                const pc of Object.values(this.peers)
            ) {

                const sender =
                    pc._teacherVideoSender ||
                    pc.getSenders().find(
                        sender =>
                            sender.track?.kind === "video"
                    );


                if (sender) {

                    await sender.replaceTrack(
                        screenTrack
                    );
                }
            }


            // TEACHER PANEL SHOWS ONLY SCREEN

            if (localVideo) {

                localVideo.srcObject =
                    this.screenStream;


                localVideo.style.width = "100%";
                localVideo.style.height = "100%";

                localVideo.style.objectFit =
                    "contain";

                localVideo.style.objectPosition =
                    "center";

                localVideo.style.position =
                    "absolute";

                localVideo.style.inset = "0";

                localVideo.style.maxWidth = "none";

                localVideo.style.border = "none";

                localVideo.style.borderRadius = "0";
            }


            // CAMERA IS STILL RUNNING IN localStream


            screenTrack.onended = async () => {

                if (!this.screenStream) {
                    return;
                }


                this.screenStream = null;


                await this._restoreCamera(
                    localVideo
                );


                const btn =
                    document.getElementById(
                        "btn-screen"
                    );


                if (btn) {
                    btn.classList.remove("active");
                }
            };


            console.log(
                "[WebRTC] Screen sharing started"
            );


            return true;

        } catch (error) {

            console.warn(
                "[WebRTC] Screen share cancelled:",
                error
            );


            this.screenStream = null;


            return false;
        }
    }


    // =====================================================
    // RESTORE CAMERA
    // =====================================================

    async _restoreCamera(localVideo) {

        const cameraTrack =
            this.localStream
                ?.getVideoTracks()[0];


        if (!cameraTrack) return;


        for (
            const pc of Object.values(this.peers)
        ) {

            const sender =
                pc._teacherVideoSender ||
                pc.getSenders().find(
                    sender =>
                        sender.track?.kind === "video"
                );


            if (sender) {

                await sender.replaceTrack(
                    cameraTrack
                );
            }
        }


        if (localVideo) {

            localVideo.srcObject =
                this.localStream;


            localVideo.style.width = "100%";
            localVideo.style.height = "100%";

            localVideo.style.objectFit =
                "cover";

            localVideo.style.objectPosition =
                "center";

            localVideo.style.position =
                "absolute";

            localVideo.style.inset = "0";

            localVideo.style.maxWidth = "none";

            localVideo.style.border = "none";

            localVideo.style.borderRadius = "0";
        }


        console.log(
            "[WebRTC] Camera restored"
        );
    }


    // =====================================================
    // MIC
    // =====================================================

    toggleMic() {

        this.micMuted =
            !this.micMuted;


        this.localStream
            ?.getAudioTracks()
            .forEach(track => {

                track.enabled =
                    !this.micMuted;
            });


        return this.micMuted;
    }


    // =====================================================
    // CAMERA
    // =====================================================

    toggleCam() {

        this.camOff =
            !this.camOff;


        this.localStream
            ?.getVideoTracks()
            .forEach(track => {

                track.enabled =
                    !this.camOff;
            });


        return this.camOff;
    }


    // =====================================================
    // REMOVE PEER
    // =====================================================

    removePeer(peerId) {

        const pc =
            this.peers[peerId];


        if (pc) {

            pc.close();

            delete this.peers[peerId];
        }
    }


    // =====================================================
    // DISCONNECT
    // =====================================================

    disconnectAll() {

        Object.keys(this.peers)
            .forEach(peerId =>
                this.removePeer(peerId)
            );


        this.localStream
            ?.getTracks()
            .forEach(track => track.stop());


        this.screenStream
            ?.getTracks()
            .forEach(track => track.stop());


        this.screenStream = null;
    }
}


// =========================================================
// FULL MAIN VIDEO PANEL
// =========================================================

if (!document.getElementById("webrtc-full-video-css")) {

    const style =
        document.createElement("style");


    style.id =
        "webrtc-full-video-css";


    style.textContent = `

        #videoGrid,
        #video-grid,
        .video-grid,
        .video-panel,
        .video-stage,
        .video-area,
        .video-container {

            position: relative !important;

            width: 100% !important;
            height: 100% !important;

            min-width: 0 !important;
            min-height: 0 !important;

            padding: 0 !important;
            margin: 0 !important;

            overflow: hidden !important;

            display: block !important;

            background: #000 !important;
        }


        #teacherVideo,
        #video-local,
        #localVideo {

            position: absolute !important;

            inset: 0 !important;

            width: 100% !important;
            height: 100% !important;

            min-width: 100% !important;
            min-height: 100% !important;

            max-width: none !important;
            max-height: none !important;

            margin: 0 !important;
            padding: 0 !important;

            border: none !important;
            border-radius: 0 !important;

            display: block !important;

            object-fit: cover;

            object-position: center;

            background: #000 !important;
        }

    `;


    document.head.appendChild(style);
}