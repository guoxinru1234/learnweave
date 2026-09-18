"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

type AvatarState = "idle" | "speaking" | "thinking" | "greeting";

interface Props {
  state?: AvatarState;
  size?: number;
  className?: string;
  onClick?: () => void;
}

export function DigitalHuman3D({ state = "idle", size = 200, className = "", onClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const headRef = useRef<THREE.Group | null>(null);
  const mouthRef = useRef<THREE.Mesh | null>(null);
  const clockRef = useRef(new THREE.Clock());

  useEffect(() => {
    if (!containerRef.current) return;
    const w = size, h = size * 1.2;

    // Scene setup
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    camera.position.set(0, 0.3, 6);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    containerRef.current.appendChild(renderer.domElement);

    // Lighting
    scene.add(new THREE.AmbientLight(0x666688, 1.5));
    const key = new THREE.DirectionalLight(0xffffff, 2);
    key.position.set(3, 3, 5);
    scene.add(key);
    const rim = new THREE.DirectionalLight(0x818cf8, 1);
    rim.position.set(-2, 1, -2);
    scene.add(rim);

    // Materials
    const skinMat = new THREE.MeshStandardMaterial({ color: 0xfce4c8, roughness: 0.6, metalness: 0.05 });
    const hairMat = new THREE.MeshStandardMaterial({ color: 0x1e1b4b, roughness: 0.4, metalness: 0.1 });
    const clothMat = new THREE.MeshStandardMaterial({ color: 0x4f46e5, roughness: 0.3, metalness: 0.2 });
    const eyeWhiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.1 });
    const pupilMat = new THREE.MeshStandardMaterial({ color: 0x1a1a2e, roughness: 0.1 });
    const lipMat = new THREE.MeshStandardMaterial({ color: 0xd4687c, roughness: 0.3 });

    // Head group
    const headGroup = new THREE.Group();
    headRef.current = headGroup;
    scene.add(headGroup);

    // Head
    const headGeo = new THREE.SphereGeometry(1, 64, 64);
    const head = new THREE.Mesh(headGeo, skinMat);
    head.scale.set(1, 1.1, 0.9);
    headGroup.add(head);

    // Hair (upper half sphere slightly larger)
    const hairGeo = new THREE.SphereGeometry(1.02, 64, 32, 0, Math.PI * 2, 0, Math.PI * 0.55);
    const hair = new THREE.Mesh(hairGeo, hairMat);
    hair.position.y = 0.05;
    headGroup.add(hair);

    // Eyes
    const eyeGeo = new THREE.SphereGeometry(0.12, 16, 16);
    const pupilGeo = new THREE.SphereGeometry(0.07, 16, 16);
    [-0.3, 0.3].forEach((x) => {
      const eyeWhite = new THREE.Mesh(eyeGeo, eyeWhiteMat);
      eyeWhite.position.set(x, 0.15, 0.85);
      headGroup.add(eyeWhite);
      const pupil = new THREE.Mesh(pupilGeo, pupilMat);
      pupil.position.set(x, 0.13, 0.95);
      headGroup.add(pupil);
    });

    // Mouth
    const mouthGeo = new THREE.BoxGeometry(0.3, 0.02, 0.05);
    const mouth = new THREE.Mesh(mouthGeo, lipMat);
    mouth.position.set(0, -0.4, 0.85);
    mouth.scale.set(1, 1, 1);
    mouthRef.current = mouth;
    headGroup.add(mouth);

    // Neck
    const neckGeo = new THREE.CylinderGeometry(0.2, 0.25, 0.4, 32);
    const neck = new THREE.Mesh(neckGeo, skinMat);
    neck.position.y = -1.2;
    headGroup.add(neck);

    // Body
    const bodyGeo = new THREE.CylinderGeometry(0.8, 0.5, 1.5, 32);
    const body = new THREE.Mesh(bodyGeo, clothMat);
    body.position.y = -2.1;
    headGroup.add(body);

    // Collar
    const collarGeo = new THREE.TorusGeometry(0.55, 0.08, 8, 32);
    const collar = new THREE.Mesh(collarGeo, new THREE.MeshStandardMaterial({ color: 0x818cf8, roughness: 0.2, metalness: 0.3 }));
    collar.position.y = -1.15;
    collar.rotation.x = Math.PI / 2;
    headGroup.add(collar);

    // Render loop
    let animId: number;
    function animate() {
      animId = requestAnimationFrame(animate);
      const t = clockRef.current.getElapsedTime();
      headGroup.position.y = Math.sin(t * 1.2) * 0.05;
      headGroup.rotation.y += 0.002;
      renderer.render(scene, camera);
    }
    animate();

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
      scene.clear();
      if (containerRef.current?.contains(renderer.domElement)) {
        containerRef.current.removeChild(renderer.domElement);
      }
    };
  }, [size]);

  // State-driven animations
  useEffect(() => {
    if (!mouthRef.current) return;
    let interval: NodeJS.Timeout;
    if (state === "speaking") {
      interval = setInterval(() => {
        mouthRef.current!.scale.y = 0.5 + Math.random() * 8;
        mouthRef.current!.position.y = -0.4 + Math.random() * 0.05;
      }, 80);
    } else {
      mouthRef.current!.scale.y = 1;
      mouthRef.current!.position.y = -0.4;
    }
    return () => clearInterval(interval);
  }, [state]);

  return (
    <div className={`relative ${className}`} onClick={onClick}>
      <div ref={containerRef} style={{ width: size, height: size * 1.2 }} />
      <div className="absolute -bottom-1 left-1/2 -translate-x-1/2">
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/60 text-indigo-600 dark:text-indigo-300 font-medium whitespace-nowrap">
          {state === "idle" && "AI 教师"}
          {state === "speaking" && "讲解中..."}
          {state === "thinking" && "思考中..."}
          {state === "greeting" && "你好!"}
        </span>
      </div>
    </div>
  );
}
