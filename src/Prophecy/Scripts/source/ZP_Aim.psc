Scriptname ZP_Aim Hidden
{Zenderal: Papyrus natives in ZenProphecyRage.dll (1.10.0 and later, src/Prophecy/rage). Papyrus has no camera.}

; The render camera (WorldRootCamera) and its forward axis (the camera root's +Y, where the crosshair points):
; [position x, y, z, forward x, y, z], world units and a unit vector; an empty array with no camera, and None when the
; DLL is missing (unbound native). Whisper's Soul Cleave aims along it.
Float[] Function CameraAim() Global Native

; 1.11.0: the ground straight below a reference, for Caldera's eruption (a ragdoll's position rides its body): a
; pathing-pick ray from afUp above its position to afDown below that stops only on terrain, statics and anim statics
; (1.12.0: it passes through trees, water, invisible walls, collision boxes, debris and the transparent layers; never
; actors, props or clutter). [z, collision layer] of the ground hit; an empty array with none, and None when the DLL
; is missing. Each call is logged in ZenProphecyRage.log.
Float[] Function GroundBelow(ObjectReference akRef, Float afUp, Float afDown) Global Native

; 1.12.0: lays a flat, disk-shaped reference on the ground's slope round it (Caldera's cracked field): ground rays at
; its centre and on two rings (0.45 and 0.9 of afRadius), a plane fitted through them, its 3D turned to that plane
; (its own spin kept, at most 35 degrees) with its centre afLift above it. Runs on the main thread a moment later; its
; 3D must be loaded (Is3DLoaded). False when it cannot start. Logged in ZenProphecyRage.log.
Bool Function LayOnGround(ObjectReference akRef, Float afRadius, Float afLift) Global Native
