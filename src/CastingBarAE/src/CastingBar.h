#pragma once

#include "StateController.h"

using EventResult = RE::BSEventNotifyControl;
using MessageResult = RE::UI_MESSAGE_RESULTS;
using MessageType = RE::UI_MESSAGE_TYPE;

class CastingBar : public RE::IMenu
{
public:

	static constexpr const char* MENU_PATH = "CastingBar";
	static constexpr const char* MENU_NAME = "CastingBar";

	// Zenderal: set from the SKSE Menu Framework page (render thread), applied in AdvanceMovie
	static inline std::atomic<const char*> PreviewMovie{ nullptr };
	static inline std::atomic<bool> LayoutDirty{ false };

	CastingBar();
	~CastingBar();

	static RE::IMenu* Creator() { return new CastingBar(); }

	static void Register();
	static void Show();
	static void Hide();

	void LoadMovie(const char* a_movie);
	void SetPercent(float a_percent);
	void FadeOut();

	MessageResult ProcessMessage(RE::UIMessage& a_message) override;
	void AdvanceMovie(float a_interval, std::uint32_t a_currentTime) override;

private:

	void ToggleVisibility(bool a_visible) { uiMovie->SetVisible(a_visible); };

	void ApplyLayout();
	void UpdatePreview();
	void UpdateVisibility();

	void OnShow();
	void OnHide();

	std::unique_ptr<StateController> controller;

	bool displayed = false;
	const char* currentMovie = nullptr;
	const char* shownPreview = nullptr;
	std::optional<bool> shownVisible;
};
