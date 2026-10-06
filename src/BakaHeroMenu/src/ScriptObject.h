#pragma once

namespace ScriptObject
{
	auto FromForm(const RE::TESForm* a_form, std::string_view a_scriptName)
		-> std::optional<RE::BSTSmartPointer<RE::BSScript::Object>>
	{
		// ZP: upstream assumes the form exists; without BakaHeroMenu.esp the MCM quest is null
		if (!a_form)
			return std::nullopt;

		if (const auto vm = RE::BSScript::Internal::VirtualMachine::GetSingleton())
		{
			if (const auto policy = vm->GetObjectHandlePolicy())
			{
				const auto type = static_cast<RE::VMTypeID>(a_form->GetFormType());
				const auto handle = policy->GetHandleForObject(type, a_form);
				if (!a_scriptName.empty())
				{
					RE::BSTSmartPointer<RE::BSScript::Object> object;
					if (vm->FindBoundObject(handle, a_scriptName.data(), object))
					{
						return object;
					}
				}
			}
		}

		return std::nullopt;
	}

	auto FromAlias(const RE::BGSBaseAlias* a_alias, std::string_view a_scriptName)
		-> std::optional<RE::BSTSmartPointer<RE::BSScript::Object>>
	{
		// ZP: upstream assumes the form exists; without BakaHeroMenu.esp the MCM quest is null
		if (!a_alias)
			return std::nullopt;

		if (const auto vm = RE::BSScript::Internal::VirtualMachine::GetSingleton())
		{
			if (const auto policy = vm->GetObjectHandlePolicy())
			{
				const auto type = a_alias->GetVMTypeID();
				const auto handle = policy->GetHandleForObject(type, a_alias);
				if (!a_scriptName.empty())
				{
					RE::BSTSmartPointer<RE::BSScript::Object> object;
					if (vm->FindBoundObject(handle, a_scriptName.data(), object))
					{
						return object;
					}
				}
			}
		}

		return std::nullopt;
	}

	auto GetVariable(RE::BSTSmartPointer<RE::BSScript::Object> a_object, std::string_view a_variableName)
		-> std::optional<RE::BSScript::Variable*>
	{
		constexpr auto INVALID = static_cast<std::uint32_t>(-1);

		std::uint32_t idx{ INVALID }, off{ 0 };
		for (auto cls = a_object->type.get(); cls; cls = cls->GetParent())
		{
			const auto vars = cls->GetVariableIter();
			if (idx == INVALID)
			{
				if (vars)
				{
					for (std::uint32_t i = 0; i < cls->GetNumVariables(); i++)
					{
						const auto& var = vars[i];
						if (var.name == a_variableName)
						{
							idx = i;
							break;
						}
					}
				}
			}
			else
			{
				off += cls->GetNumVariables();
			}
		}

		if (idx == INVALID)
		{
			SKSE::log::debug(
				"Variable {} does not exist on script {}"sv,
				a_variableName,
				a_object->GetTypeInfo()->GetName());
			return std::nullopt;
		}

		return std::addressof(a_object->variables[idx + off]);
	}

	auto GetBool(RE::BSTSmartPointer<RE::BSScript::Object> a_object, std::string_view a_variableName)
		-> std::optional<bool>
	{
		if (auto variable = GetVariable(a_object, a_variableName))
			return (*variable)->GetBool();
		return std::nullopt;
	}

	auto GetSInt(RE::BSTSmartPointer<RE::BSScript::Object> a_object, std::string_view a_variableName)
		-> std::optional<std::int32_t>
	{
		if (auto variable = GetVariable(a_object, a_variableName))
			return (*variable)->GetSInt();
		return std::nullopt;
	}
};
