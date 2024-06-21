

# Options
  * **soul\_shards** : Specify initial Soul Shard amount
  * **default\_pet** : Specify default main pet (_imp_, _voidwalker_, _incubus_, _succubus_, _sayaad_, _felhunter_, Demo only: _felguard_)
  * **disable_felstorm** : Disables automatic usage of Felstorm for Demonology's main Felguard

# Actions
  * _interrupt_ : Will use an appropriate pet interrupt (Spell Lock/Axe Toss) if target is casting and a valid pet is currently active

# Expressions
  * _last\_cast\_imps_ : Number of Wild Imps with one cast remaining
  * _two\_cast\_imps_ : Number of Wild Imps with two casts remaining
  * _igb\_ratio_ : Calculates number of Imp Gang Bosses divided by total Wild Imps (incl. IGBs)
  * _time\_to\_shard_ : Estimated time until Agony next generates a Soul Shard
  * _pet\_count_ : Total number of (Warlock) pets currently active
  * _havoc\_active_ : Boolean checking if Havoc is currently applied to _any_ target whatsoever
  * _havoc\_remains_ : Time remaining on the Havoc debuff, wherever it is
  * _incoming\_imps_ : Number of Wild Imps which will be spawning from Hand of Gul'dan but have not yet spawned
  * _can\_seed_ : Returns true if there is a valid target for Seed of Corruption which does not have a Seed DoT or Seed in-flight already
  * _time\_to\_imps.N.remains_ : Returns the time to having N total Wild Imps, including those scheduled to be spawned. If N is greater than the total expected, returns time to last imp. "all" can be used in place of a value as well.