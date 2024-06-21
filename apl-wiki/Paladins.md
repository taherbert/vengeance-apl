**Is there an error? Something missing? Funky grammar? Do not hesitate to leave a comment.**



# Textual configuration interface
_This section is a part of the [TCI](TextualConfigurationInterface) reference._

Regular spells are not mentioned here, you just have to follow the standard [names formatting rules](TextualConfigurationInterface#Names_formatting).

## Buffs
Regular buffs for this class are not mentioned here, you just have to follow the standard [names formatting rules](TextualConfigurationInterface#Names_formatting.md). Also, don't forget that set bonuses are added as buffs to a character. Buffs can be used in conditional expressions for actions, see [ActionLists#Buffs\_and\_debuffs](ActionLists#Buffs_and_debuffs).

## Time Until Next HPG
`time_to_hpg` will return the time until the next holy power generator is available, in seconds. It will also enforce a minimum time equal to the current GCD (i.e. if there's a holy power generator that is off cooldown, but the GCD isn't up for another 350 ms, this will evaluate to 0.350).
```
  #cast TV if we're at 5 holy power and a holy power generator is available next GCD
  actions+=/templars_verdict,if=holy_power>=5&time_to_hpg<=gcd.max
```
Note that this does not do any fancy calculus to figure out if the next GCD actually _will_ be a HPG. It _only_ returns the time until the next HPG is available. If your action list prioritizes other spells over HPGs, then the time until the next HPG is actually cast could be longer than `time_to_hpg`. It should never be shorter, however.

Note#2: This is only supported for Retribution Paladin at the moment.

## Blessed Hammer strikes
Blessed Hammer can hit multiple times depending on the size of the target in-game. To reproduce that behavior, the blessed_hammer action has a `strikes` option (float, default: 2, min: 1, max: 10) that can be used to specified the number of time each cast will hit each target.
If the number has decimals, they will be used as a chance to generate an extra strike for every blessed hammer cast.
```
# Hit every enemy 3 times per blessed hammer cast
actions+=/blessed_hammer,strikes=3
```

## Consecration Precombat time
When Consecration is included in the precombat APL, the spell will be used with a special behaviour based on the precombat_time option given to it (default: 2s). The ground aoe's start time will be delayed by 1s to simulate the time the boss takes to run into it. Its duration and cooldown will also be adjusted accordingly.
>Negative values will be handled the same way as some users may find it more intuitive (-3 is 3s before combat starts). The absolute value has to be lower than consecration's total duration, and higher than the player's based gcd duration (1.5s).
```
# Use consecration 3s before combat starts
actions.precombat=consecration,precombat_time=3
```

# Reports
We only document here non-obvious entries.

## Procs
  * parry\_haste: the number of times your swings have been hasted after you parried an attack.