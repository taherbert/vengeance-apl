-- function (all, event, _, subEvent, _, sourceGUID, _, _, _, _, destName, _, _, spellId)
--   -- Only listen for the player's casts and ignore if it's not a spell cast success
--   if sourceGUID ~= UnitGUID("player") or subEvent ~= "SPELL_CAST_SUCCESS" then return end

--   local trackedSpells = {
--     [225919] = {souls=1, duration=0.85}, -- Fracture MH
--     [225921] = {souls=1, duration=0.85}, -- Fracture OH
--     [207407] = {souls=3, duration=0.85}, -- Soul Carver initial
--     [204596] = {souls=1, duration=1.85}, -- Sigil of Flame
--     [207684] = {souls=1, duration=1.85}, -- Sigil of Misery
--     [202137] = {souls=1, duration=1.85}, -- Sigil of Silence
--     [202138] = {souls=1, duration=1.85}, -- Sigil of Chains
--     [390163] = {souls=4, duration=1.85}, -- Elysian Decree
--   }

--   if not trackedSpells[spellId] then return end

--   local quickenedSigils = {204596, 207684, 202137, 202138, 390163}
--   local soulSigils = {204596, 207684, 202137, 202138, 390163}

--   -- check for quickened sigils
--   if not IsPlayerSpell(209281) then
--     print(select(5, GetTalentInfo(8, 4)))
--     for _, spellId in ipairs(quickenedSigils) do
--       trackedSpells[spellId].duration = trackedSpells[spellId].duration + 1
--     end
--   end

--   -- check for soul sigils
--   if not IsPlayerSpell(395446) then
--     print(select(5, GetTalentInfo(8, 3)))
--     for _, spellId in ipairs(soulSigils) do
--       trackedSpells[spellId].souls = trackedSpells[spellId].souls - 1
--     end
--   end

--   -- What we're going to add to our TSU
--   local state = {
--     changed = true,
--     show = true,
--     progressType = "timed",
--     autoHide = true,
--     duration = trackedSpells[spellId].duration,
--   }

--   -- add the TSU for the spell
--   if trackedSpells[spellId].souls > 0 then
--     for i = 1, trackedSpells[spellId].souls do
--       table.insert(all, state)
--     end
--   end

--   -- Soul Carver needs to add 3 more TSUs for the 3 souls over time
--   if spellId == 207407 then
--     for i = 1, 3 do
--       local carver = {
--         changed = true,
--         show = true,
--         progressType = "timed",
--         autoHide = true,
--         duration = 1.85 + i,
--       }
--       table.insert(all, carver)
--     end
--   end


--   return true
-- end



function(allstates)
  if not aura_env.last or GetTime() - aura_env.last > aura_env.config.throttle then
    aura_env.last = GetTime()

    local can_spb = false
    local target_count = 0
    local brand_count = 0

    for i = 1, 40 do
      local unit = "nameplate"..i
      if UnitCanAttack("player", unit) and (not aura_env.config.combat or UnitAffectingCombat(unit)) and WeakAuras.CheckRange(unit, aura_env.config.range, "<=") then
        target_count = target_count + 1
        if AuraUtil.FindAuraByName("Fiery Brand", unit, "HARMFUL|PLAYER") then
          brand_count = brand_count + 1
        end
      end
    end

    local souls = select(3, AuraUtil.FindAuraByName("Soul Fragments", "player")) or 0

    if brand_count > 0 then
      if target_count == 1 and souls >= 5 then
        can_spb = true
      elseif target_count > 1 and target_count <= 5 and souls >= 4 then
        can_spb = true
      elseif target_count > 5 and souls >= 3 then
        can_spb = true
      end
    else
      if target_count > 1 and target_count <= 5 and souls >= 5 then
        can_spb = true
      elseif target_count > 5 and souls >= 4 then
        can_spb = true
      end
    end

    if can_spb then
      allstates[""] = allstates[""] or {show = true}
      allstates[""].changed = true
      return true
    elseif allstates[""] then
      allstates[""].show = false
      allstates[""].changed = true
      return true
    end
  end
end


for i = 1, 5 do
  local soul = WeakAuras.GetRegion("Jom VDH: Soul " .. i)
  soul:Color(1, 0, 0, 1)
end

for i = 1, 5 do
  local soul = WeakAuras.GetRegion("Jom VDH: Soul " .. i)
  soul:Color(171, 70, 163, 1)
end