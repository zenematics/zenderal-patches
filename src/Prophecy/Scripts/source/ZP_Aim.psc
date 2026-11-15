Scriptname ZP_Aim Hidden
{Zenderal: Papyrus natives in ZenProphecyRage.dll (1.10.0 and later, src/Prophecy/rage). Papyrus has no camera.}

; The render camera (WorldRootCamera) and its forward axis (the camera root's +Y, where the crosshair points):
; [position x, y, z, forward x, y, z], world units and a unit vector; an empty array with no camera, and None when the
; DLL is missing (unbound native). Whisper's Soul Cleave aims along it.
Float[] Function CameraAim() Global Native
