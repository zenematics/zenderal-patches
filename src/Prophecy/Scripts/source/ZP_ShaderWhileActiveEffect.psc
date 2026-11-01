Scriptname ZP_ShaderWhileActiveEffect extends ActiveMagicEffect
{Plays an effect shader on the target for as long as this effect is active - for a conditioned ability effect (Shade
Veil: while sneaking). A HitShader on such an effect did not show (in game, 2026-10-28: the effect was active, no mist);
a condition flip does start and finish the effect, so its script sees each one.}

EffectShader Property Shader Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Shader.Play(akTarget, -1.0)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Shader.Stop(akTarget)
EndEvent
