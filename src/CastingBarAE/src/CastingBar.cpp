#include "CastingBar.h"
#include "Settings.h"

using namespace RE;


CastingBar::CastingBar()
{
	logger::trace("CastingBar::Ctor");

	depthPriority = 0;

	menuFlags.set(UI_MENU_FLAGS::kAlwaysOpen);
	menuFlags.set(UI_MENU_FLAGS::kRequiresUpdate);
	menuFlags.set(UI_MENU_FLAGS::kAllowSaving);

	auto player = PlayerCharacter::GetSingleton();
	controller.reset(new StateController(this, player));
}

CastingBar::~CastingBar() 
{
    logger::trace("CastingBar::Dtor");
}

void CastingBar::Register()
{
    if (auto ui = UI::GetSingleton()) {
        ui->Register(MENU_NAME, Creator);
    }
}

void CastingBar::Show() 
{
    if (auto queue = UIMessageQueue::GetSingleton()) {
        queue->AddMessage(MENU_NAME, UI_MESSAGE_TYPE::kShow, nullptr);
    }
}

void CastingBar::Hide() 
{
    if (auto queue = UIMessageQueue::GetSingleton()) {
        queue->AddMessage(MENU_NAME, UI_MESSAGE_TYPE::kHide, nullptr);
    }
}

MessageResult CastingBar::ProcessMessage(UIMessage& a_message)
{
	if (a_message.menu == MENU_NAME) {

		switch (a_message.type.get()) {
		case MessageType::kShow:
		case MessageType::kReshow:
			OnShow();
			break;
		case MessageType::kHide:
		case MessageType::kForceHide:
			OnHide();
			break;
		}
    }

    return IMenu::ProcessMessage(a_message);
}

void CastingBar::AdvanceMovie(float a_interval, std::uint32_t a_currentTime) 
{
    IMenu::AdvanceMovie(a_interval, a_currentTime);

	UpdatePreview();
	if (!shownPreview) {
		controller->Update();
	}

	if (uiMovie && LayoutDirty.exchange(false)) {
		ApplyLayout();
	}

	UpdateVisibility();
}

// Zenderal: the menu framework's "show widget" option holds one widget on screen at 60% for positioning
void CastingBar::UpdatePreview()
{
	const char* wanted = PreviewMovie.load();
	if (wanted != shownPreview) {
		if (wanted) {
			LoadMovie(wanted);
		} else if (uiMovie) {
			FadeOut();
		}
		shownPreview = wanted;
	}
	if (shownPreview && uiMovie) {
		SetPercent(0.6f);
	}
}

// Zenderal: Ultimate Immersion Toggle hides the HUD by setting "HUD Menu" _root._alpha to 0; follow it
void CastingBar::UpdateVisibility()
{
	if (!uiMovie) {
		return;
	}

	bool visible = true;
	if (Settings::HideWithHUD) {
		if (auto ui = UI::GetSingleton()) {
			if (auto hud = ui->GetMenu(HUDMenu::MENU_NAME); hud && hud->uiMovie) {
				GFxValue alpha;
				if (hud->uiMovie->GetVariable(&alpha, "_root._alpha") && alpha.IsNumber() && alpha.GetNumber() <= 0.0) {
					visible = false;
				}
			}
		}
	}

	if (shownVisible != visible) {
		ToggleVisibility(visible);
		shownVisible = visible;
	}
}

void CastingBar::LoadMovie(const char* a_movie)
{
	//logger::trace("CastingBar::LoadMovie: {}", a_movie);

	auto scaleform = BSScaleformManager::GetSingleton();
	scaleform->LoadMovie(this, this->uiMovie, a_movie);

	currentMovie = a_movie;
	shownVisible.reset();
	ApplyLayout();
}

void CastingBar::SetPercent(float a_percent)
{
	const GFxValue value = a_percent * 100.0f;
	
	uiMovie->Invoke("meter.doShow", nullptr, nullptr, 0);
	uiMovie->Invoke("meter.setMeterPercent", nullptr, &value, 1);

	displayed = true;
}

void CastingBar::FadeOut()
{
	if (displayed) {
		uiMovie->Invoke("meter.doFadeOut", nullptr, nullptr, 0);
		displayed = false;
	}
}

void CastingBar::ApplyLayout() 
{
	const auto& layout = Settings::LayoutFor(currentMovie ? currentMovie : "");

	const GFxValue x_pos = layout.PositionX;
	const GFxValue y_pos = layout.PositionY;
	const GFxValue x_scl = layout.ScaleX;
	const GFxValue y_scl = layout.ScaleY;

    GFxValue posArray[5] = {x_pos, y_pos, 0.0, x_scl, y_scl};

    uiMovie->Invoke("meter.setLocation", nullptr, posArray, 5);

	uiMovie->SetMouseCursorCount(0); // disable input
}

void CastingBar::OnShow()
{
	//logger::trace("CastingBar::OnShow");
};

void CastingBar::OnHide() 
{
	//logger::trace("CastingBar::OnHide");
};
