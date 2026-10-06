#pragma once

#include "Manager.h"
#include "MCM.h"

namespace Events
{
	class MenuOpenCloseEvent :
		public REX::Singleton<MenuOpenCloseEvent>,
		public RE::BSTEventSink<RE::MenuOpenCloseEvent>
	{
	public:
		virtual RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* a_event, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override
		{
			if (a_event && a_event->opening && a_event->menuName == ZP::HeroMenuName)
			{
				if (auto ui = RE::UI::GetSingleton())
					if (auto view = ui->GetMovieView(ZP::HeroMenuName);
						view &&
						view->GetMovieDef() &&
						ZP::IContains(view->GetMovieDef()->GetFileURL(), "00E_HeroMenu.swf"sv))
					{
						Manager::GetSingleton()->UpdateCache();
						Manager::GetSingleton()->UpdateMenuName(view);
					}
			}

			if (a_event && !a_event->opening && a_event->menuName == "Journal Menu"sv)
			{
				MCM::GetSingleton()->LoadSettings();
			}

			return RE::BSEventNotifyControl::kContinue;
		}
	};

	static void Install()
	{
		if (auto ui = RE::UI::GetSingleton())
			ui->AddEventSink<RE::MenuOpenCloseEvent>(MenuOpenCloseEvent::GetSingleton());
	}
}
