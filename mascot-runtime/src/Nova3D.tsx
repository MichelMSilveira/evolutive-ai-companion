import { Suspense, useEffect, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Bounds, OrbitControls, useAnimations, useGLTF } from "@react-three/drei";
import * as THREE from "three";

function NovaModel() {
  const group = useRef<THREE.Group>(null);
  const { scene, animations } = useGLTF("/assets/nova/nova-3d-prototype.glb");
  const { actions } = useAnimations(animations, group);

  useEffect(() => {
    const action = Object.values(actions)[0];
    action?.reset().fadeIn(0.2).play();
    return () => { action?.fadeOut(0.2); };
  }, [actions]);

  useFrame(({ clock }) => {
    if (group.current) group.current.position.y = Math.sin(clock.elapsedTime * 2.2) * 0.025;
  });

  return <group ref={group} dispose={null} scale={1.45} position={[0, -1.05, 0]} rotation={[0, 0.2, 0]}>
    <primitive object={scene} />
  </group>;
}

export function Nova3D() {
  return <Canvas camera={{ position: [4.5, -6.5, 3.2], fov: 32 }} dpr={[1, 2]}>
    <ambientLight intensity={1.8} />
    <directionalLight position={[3, -4, 7]} intensity={3.2} color="#dffcff" />
    <directionalLight position={[-4, 3, 2]} intensity={1.4} color="#6debd8" />
    <Suspense fallback={null}><Bounds fit clip observe margin={1.15}><NovaModel /></Bounds></Suspense>
    <OrbitControls enablePan={false} enableZoom={false} enableRotate={false} />
  </Canvas>;
}

useGLTF.preload("/assets/nova/nova-3d-prototype.glb");
