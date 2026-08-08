"use client";

import { useEffect, useRef, useState } from "react";

export function CameraCaptureModal({
  onCapture,
  onClose,
}: {
  onCapture: (file: File) => void;
  onClose: () => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    navigator.mediaDevices
      // "ideal" (not required) so this still works on a laptop with only a
      // single front-facing webcam, not just phones with a rear camera.
      .getUserMedia({ video: { facingMode: { ideal: "environment" } } })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch(() => {
        setError(
          "Couldn't access the camera. Check your browser's camera permission for this site and try again."
        );
      });

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const handleCapture = () => {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        onCapture(new File([blob], "photo.jpg", { type: "image/jpeg" }));
      },
      "image/jpeg",
      0.9
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-paper-raised p-5 shadow-lg">
        <h2 className="mb-3 font-semibold text-ink">Take a photo</h2>
        {error ? (
          <p className="mb-4 text-sm text-redink">{error}</p>
        ) : (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="mb-4 block max-h-[60vh] w-full rounded-md bg-black"
          />
        )}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleCapture}
            disabled={!!error}
            className="flex-1 rounded-md bg-ledger px-3 py-2 text-sm font-semibold text-paper disabled:opacity-50"
          >
            Capture
          </button>
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-md border border-rule px-3 py-2 text-sm text-pencil"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
