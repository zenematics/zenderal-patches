#pragma once

#include "Manager.h"

namespace Hooks
{
	class hkProcessEvent
	{
	private:
		static constexpr std::array<const char*, 18> SkillNames{
			"einhand",           // OneHanded
			"zweihand",          // TwoHanded
			"bogenkunst",        // Archery
			"parade",            // Block
			"schmieden",         // Smithing
			"schwereruestung",   // HeavyArmor
			"leichteruestung",   // LightArmor
			"taschendiebstahl",  // Pickpocket
			"schlossknacken",    // Lockpicking
			"schleichen",        // Sneak
			"alchimie",          // Alchemy
			"rethorik",          // Speech
			"mentalismus",       // Alteration
			"entropie",          // Conjuration
			"elementarismus",    // Destruction
			"psionik",           // Illusion
			"lichtmagie",        // Restoration
			"verzauberung",      // Enchanting
		};

	private:
		static auto GetSelectedSkill(RE::GFxValue& a_mc)
			-> std::optional<std::int32_t>
		{
			for (std::int32_t i = 0; i < 18; i++)
			{
				RE::GFxValue member;
				if (a_mc.GetMember(SkillNames[i], &member))
				{
					RE::GFxValue visible;
					if (auto success = member.GetMember("_visible", &visible);
						success && visible.IsBool() && visible.GetBool())
					{
						return i;
					}
				}
			}

			return std::nullopt;
		};

	private:
		static auto ProcessEvent(RE::MenuControls* a_this, RE::InputEvent* const* a_event, RE::BSTEventSource<RE::InputEvent*>* a_source)
			-> RE::BSEventNotifyControl
		{
			if (a_event && *a_event)
			{
				if (auto ui = RE::UI::GetSingleton();
					ui && ui->IsMenuOpen(ZP::HeroMenuName) && !ui->IsMenuOpen("Console"sv))
				{
					RE::GFxValue movieclip;
					if (auto view = ui->GetMovieView(ZP::HeroMenuName);
						view &&
						view->GetMovieDef() &&
						ZP::IContains(view->GetMovieDef()->GetFileURL(), "00E_HeroMenu.swf"sv) &&
						view->GetVariable(&movieclip, "heromenu_mc.description"))
					{
						if (auto buttonEvent = (*a_event)->AsButtonEvent();
							buttonEvent && buttonEvent->IsDown())
						{
							if (Manager::GetSingleton()->QOverrideMessage())
								return _ProcessEvent(a_this, a_event, a_source);

							if (buttonEvent->QUserEvent() == "Accept"sv || buttonEvent->QUserEvent() == "Click"sv)
							{
								if (auto idx = GetSelectedSkill(movieclip))
									Manager::GetSingleton()->TryIncreaseSkill(*idx);
							}
							else if (buttonEvent->QUserEvent() == "Cancel"sv || (buttonEvent->QUserEvent() == "Quick Stats"sv))
							{
								if (auto queue = RE::UIMessageQueue::GetSingleton())
									queue->AddMessage(ZP::HeroMenuName, RE::UI_MESSAGE_TYPE::kHide, nullptr);
							}
						}
					}
				}
			}

			return _ProcessEvent(a_this, a_event, a_source);
		}

		// ZP: libxse's REL::THookVFT replaced with CommonLibSSE-NG's write_vfunc (vfunc 1 of BSTEventSink<InputEvent*>)
		inline static REL::Relocation<decltype(&ProcessEvent)> _ProcessEvent;

	public:
		static void Install()
		{
			REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_MenuControls[0] };
			_ProcessEvent = vtbl.write_vfunc(0x01, ProcessEvent);
		}
	};

	static void Install()
	{
		hkProcessEvent::Install();
	}
}
