Scriptname ZP_GrantPointsOnRead extends ActiveMagicEffect
{Zenderal - Learning Books Grant Learning Points. Grants Value point(s) of the Points global
 (Lernpunkte 031ACB or Handwerkspunkte 085A79) and shows Notification. Modeled on SureAI's
 _00E_Lehrbuch_Plus2SkillpointsScript / _00E_Erinnerungslehrbuch. Deliberately never touches
 TalentPoints or the dragonsouls AV - those are Memory Points, a separate currency.}

GlobalVariable Property Points Auto
Message Property Notification Auto
Int Property Value = 1 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)

	Points.Mod(Value)
	Notification.Show(Value)

EndEvent
