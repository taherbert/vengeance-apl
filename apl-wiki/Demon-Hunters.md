**Is there an error? Something missing? Funky grammar? Do not hesitate to leave a comment.**



# Textual configuration interface
_This section is a part of the [TCI](TextualConfigurationInterface) reference._

## Options

- **initial_fury** (0–120, default: 0): Amount of fury the demon hunter is initialized with.
- **target_reach** (default: -1.0): Override for target's hitbox size, relevant for Fel Rush and Vengeful Retreat. -1.0 uses default SimC value.
- **movement_direction_factor** (1.0–2.0, default: 1.8): Relative directionality for movement events, 1.0 being directly away and 2.0 being perpendicular.
- **soul_fragment_movement_consume_chance** (0.0–1.0, default: 0.85): Chance of souls to be incidentally picked up on any movement ability due to being in pickup range.
- **fodder_to_the_flame_initiative_chance** (0.0–1.0, default: 0.85): Chance to proc initiative off of the fodder demon (ie. not get damaged by it first).
- **fodder_to_the_flame_kill_seconds** (0–10, default: 4): Time in seconds for the demon spawned by Fodder to the Flame to die.
- **darkglare_boon_cdr_high_roll_seconds** (6–24, default: 18): How many seconds of CDR from Darkglare Boon is considered a high roll.

## Expressions

* **soul_fragments**: The number of active, consumable soul fragments.
* **greater_soul_fragments**: The number of active, consumable greater soul fragments.
* **lesser_soul_fragments**: The number of active, consumable lesser soul fragments.
* **demon_soul_fragments**: The number of active, consumable demon soul fragments.

All soul fragment expressions can be modified via filters in the form `soul_fragments.X` where `X` is:
- **active**: The number of active, consumable soul fragments (identical to using no filter).
- **inactive**: The number of soul fragments which have been spawned but are not yet activated.
- **total**: The total number of spawned soul fragments (active and inactive).

## Special Actions

* **pick_up_fragment**: Move to and consume a nearby Soul Fragment. Any if expression (if provided) will be evaluated at both the start of the movement and when reaching the fragment, which may result in the action being executed without a fragment being consumed. See action options section for more details on how to use this action.

## Action Options

* **metamorphosis,landing_distance=x**: How far away from the target to land with Havoc's Metamorphosis. Valid range: 0–40.
* **pick_up_fragment,type=x**: The type of soul fragment to be picked up. Valid options: *greater*, *lesser*, *demon*, *all* or *any*. Default: *all*
* **pick_up_fragment,mode=x**: The mode that determines which fragments should be prioritized. Valid options: *closest* or *nearest* or *close* or *near*, *newest* or *new*, *oldest* or *old*. Default: *oldest*

# Reporting

## Procs

### General

* **delayed_aa_out_of_range**: An auto-attack was delayed due to the player being outside of melee range of the target.
* **delayed_aa_cast**: An auto-attack was delayed due to the player casting a spell.
* **delayed_aa_channel**: An auto-attack was delayed due to the player channeling a spell.
* **soul_fragment_greater**: A greater soul fragment was consumed.
* **soul_fragment_lesser**: A lesser soul fragment was consumed.
* **soul_fragment_greater_demon**: A greater demon soul fragment was consumed.
* **soul_fragment_empowered_demon**: An empowered (Fodder to the Flame) demon soul was consumed.
* **felblade_reset**: Felblade's cooldown was reset. 
* **relentless_pursuit**: The Hunt's cooldown was reduced due to an enemy dying with the DoT active.

### Havoc

* **demonic_appetite**: A soul fragment was spawned by a Demonic Appetite proc. 
* **demons_bite_in_meta**: Demon's Bite was used during Metamorphosis. This is intended to be used as a optimization metric for APL fury pooling logic.
* **chaos_strike_in_essence_break**: Chaos Strike was used during Essence Break.
* **annihilation_in_essence_break**: Annihilation was used during Essence Break.
* **blade_dance_in_essence_break**: Blade Dance was used during Essence Break.
* **death_sweep_in_essence_break**: Death Sweep was used during Essence Break.
* **chaos_strike_in_serrated_glaive**: Chaos strike was used during  Serrated Glaive.
* **annihilation_in_serrated_glaive**: Annihilation was used during  Serrated Glaive.
* **eye_beam_tick_in_serrated_glaive**: An Eye Beam tick occurred during Serrated Glaive.
* **shattered_destiny**: The cooldown of Metamorphosis was reduced by Shattered Destiny.
* **eye_beam_canceled**: Eye Beam was canceled early.

### Vengeance

* **soul_fragment_expire**: A soul fragment expired without being consumed. 
* **soul_fragment_overflow**: A soul fragment was spawned while the player was already at the maximum number of soul fragments of that type.
* **soul_fragment_from_shear**: A soul fragment was spawned from Shear.
* **soul_fragment_from_fracture**: A soul fragment was spawned from Fracture.
* **soul_fragment_from_fallout**: A soul fragment was spawned from Fallout.
* **soul_fragment_from_meta**: An additional soul fragment was spawned from Shear or Fracture during Metamorphosis.