-- One-time UE4SS helper for SMT5V save research.
--
-- Install as:
--   <Game>\Binaries\Win64\Mods\SaveLab\Scripts\main.lua
-- and enable the SaveLab mod the same way the bundled mods are enabled.
--
-- Keybinds:
--   F8  list candidate save/demon/item classes and instances
--   F9  DumpAllObjects()
--   F10 GenerateSDK()
--
-- This script only reads and dumps; it does not modify the game or the save.

local CANDIDATE_CLASSES = {
    "SaveGame",
    "SaveGameBase",
    "SMT5VSaveGame",
    "SMT5VSaveGame_C",
    "GameSave",
    "GameSaveData",
    "SaveData",
    "PlayerData",
    "DemonData",
    "DemonSaveData",
    "ItemData",
    "ItemSaveData",
    "SysSave",
}

local function list_candidates()
    print("[SaveLab] Searching for candidate classes...\n")
    for _, class_name in ipairs(CANDIDATE_CLASSES) do
        local ok, objects = pcall(FindAllOf, class_name)
        if not ok then
            print(string.format("[SaveLab] %s: lookup failed (%s)\n", class_name, tostring(objects)))
        elseif objects and #objects > 0 then
            print(string.format("[SaveLab] %s: %d instance(s)\n", class_name, #objects))
            for index, object in ipairs(objects) do
                print(string.format("[SaveLab]   [%d] %s\n", index, object:GetFullName()))
            end
        else
            print(string.format("[SaveLab] %s: none\n", class_name))
        end
    end
    print("[SaveLab] Done. Use Ctrl+J or F9 for a full object dump.\n")
end

local function dump_objects()
    print("[SaveLab] Dumping all objects...\n")
    DumpAllObjects()
    print("[SaveLab] Object dump requested.\n")
end

local function generate_sdk()
    print("[SaveLab] Generating C++ headers...\n")
    GenerateSDK()
    print("[SaveLab] SDK generation requested.\n")
end

RegisterKeyBind(Key.F8, list_candidates)
RegisterKeyBind(Key.F9, dump_objects)
RegisterKeyBind(Key.F10, generate_sdk)

print("[SaveLab] Loaded. F8 = list candidates, F9 = object dump, F10 = SDK dump.\n")
