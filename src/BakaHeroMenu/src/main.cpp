#include "Events.h"
#include "Hooks.h"
#include "Manager.h"
#include "MCM.h"
#include "Translator.h"

// ZP: CommonLibSSE-NG port for Enderal SE 2.0.12 / SSE 1.5.97. Upstream's xmake rule generated the
// plugin declaration; NG's SKSEPluginInfo emits both SKSEPlugin_Version and the SKSEPlugin_Query
// that SKSE on 1.5.97 requires.
SKSEPluginInfo(
	.Version = REL::Version{ 1, 1, 0, 0 },
	.Name = "BakaHeroMenu"sv,
	.Author = "shad0wshayd3 (1.5.97 port: Zenderal)"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	void MessageHandler(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type)
		{
		case SKSE::MessagingInterface::kPostLoad:
			Hooks::Install();
			SKSE::log::info("Installed MenuControls::ProcessEvent hook");
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
			Manager::GetSingleton()->LoadSave();
			MCM::GetSingleton()->LoadSettings();
			break;
		case SKSE::MessagingInterface::kDataLoaded:
			Events::Install();
			Manager::GetSingleton()->LoadForm();
			MCM::GetSingleton()->LoadForm();
			SKSE::log::info("Data loaded: forms resolved");
			break;
		default:
			break;
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("BakaHeroMenu 1.1.0 (1.5.97 port) loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener(MessageHandler);
	return true;
}
