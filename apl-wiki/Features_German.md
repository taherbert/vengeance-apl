

# Was ist es?
> Simulationcraft ist ein freies open-source Simulationsprogramm ( siehe [FormulationVsSimulation](FormulationVsSimulation)) von World of Warcraft Kampfmechaniken: Es kann Kämpfe mit einem oder mehreren Spielern und mit einem oder vielen Zielen simulieren und erzeugt dafür detailierte Informationen. Es gibt sowohl ein Graphisches Benutzer-Interface wie auch einen Command-Line Klient.

> Da Simulationcraft eine Simulation ist, wird es nie zweimal das selbe Ergebnis liefern (Der Zufall zählt!): Das Ergebnis wird immer variieren, bleibt aber immer sehr nah am exakten Resultat, welches man im Spiel beobachten kann. Die Präzision lässt kontrollieren und erhöhen auf Kosten der Berechnungszeit. Dies kann unter Umständen zu sehr rechenzeit- und speicherintesiven Simulationen führen. Zum Schluss ist es noch wichtig, dass Simulationcraft in seinem Kern ein Kommandozeilen Programm ist, basierend auf Konfigurationsdateien, und das Graphische Benutzer-Interface wurde erst später hinzugefügt - obwohl sehr effizient, ist es im Moment noch immer rudimentär und steif.

> Da Simulationcraft - wie der Name schon sagt - eine Simulation ist, hat es auch klare Vorteile gegenüber traditionellen, analytischen Programmen wie z. B. Spreadsheets oder Rawr. Eine mathematische Formulierung zu entwicklen ist meist sehr umfangreich und hochkomplex, wohingegen die Entwicklung einer Simulation aus vielen kleinen Teilproblemen besteht. Dies hat nicht nur für die Entwicklung Konsequenzen, sondern auch für den Benutzer, in einer Welt wo Programme nur von einer handvoll Entwickler erschaffen werden:
  * **Zuverlässigkeit:** "einfach" zu entwickeln heisst auch, einfach zu überprüfen. Weiter muss ein Problem nie mathematisch Approximiert oder gewisse Funktionen ignoriert werden: Alle Machaniken und Abläufe werden eins zu eins reproduziert. Selbstverständlich können sich Fehler einschleichen, aber sie sind einfach erkannt und schnell beseitigt. Natürlich kann auch ein formal-basiertes Programm die selbe Genauigkeit erreichen, in den meisten Fällen aber hat man keine Ahnung über die Art der Genauigkeit: Das Programm ist sozusagen eine hochkomplexe Blackbox, welche nur auf Vertrauen aufbaut. Und da der Quellcode meist sehr schwer zu verstehen und zu verifizieren ist, wird dies in vielen Fällen niemand auf sich nehmen.

  * **Schnelle Updates:** Eine Simulation ist viel einfacher zu updaten: In den meisten Fällen kann man sogar Änderungen auf den PTR-Servern einbeziehen, lange before diese die Live-Server erreichen.
Simulationcraft hat es in der Vergangenheit immer wieder geschafft auf dem neuesten Stand zu sein. So konnten schon einige Wochen nach dem Release von Cataclysm für viele Klassen bereits fertige Ergebnisse präsentiert werden.


  * **Features-rich and highly configurable:** The nature of Simulationcraft allows us to provide rich informations and offer you a broader range of features, to let you change your rotations, to simulate fights the way you want, to synchronize your cooldowns with certain events, etc... Simulationcraft has tons of settings you can play with.

# Rich reports
> Simulationcraft can generate reports such as those displayed on [simulationcraft.org](http://www.simulationcraft.org/)). Most notable informations are:
  * Decomposition of the dps, such as tools like Recount or World of logs can provide.
  * Dps distribution: to understand how your dps can vary across fights because of the rng.
  * Resource gains: how much a talent or buff is important for your resources?
  * Dps timeline: to measure the importance of certain cooldowns.
  * Spells details: damage per resources, per execution time, minimum and maximum output, etc.
  * Buffs details: uptimes, real benefit, etc.
  * Etc...

> ![http://www.simulationcraft.org/images/wiki/samplegraphs.png](http://www.simulationcraft.org/images/wiki/samplegraphs.png)
# Stats weighting to compare items
> Simulationcraft can be used to compute scale factors: those are weights given to every stat so that one can compare them. The higher a scale factor, the better a stat!

> How can you use them? Our reports will provide you with link towards [Wowhead (sample)](http://www.wowhead.com/?items&filter=ub=1;gm=3;gb=1;rf=1;minle=346;wt=20:21:77:117:119:96:103:170:32;wtv=2.6373:1.2115:1.1952:1.5543:1.4658:1.5130:1.0993:1.3631:5.0913;) and [GuildOx (sample)](http://www.guildox.com/wr.asp?usr=&ser=&grp=www&Cla=1024&F=H&Int=3.2213&Spi=2.2387&spd=2.4038&mhit=2.2286&mcr=0.9007&mh=1.7434&Mr=1.1686&Ver=6) to compare your items.

> ![http://www.simulationcraft.org/images/wiki/wowhead.png](http://www.simulationcraft.org/images/wiki/wowhead.png)

# Connected to the rest of the world
> Simulationcraft can import character profiles from [Battle.net](http://us.battle.net/wow/en/), [Wowhead profiles](http://www.wowhead.com/profiles), [Chardev](http://chardev.org/?planner) and [Rawr](http://rawr.codeplex.com/).

> It provides you with link towards [Wowhead](http://www.wowhead.com/?items&filter=ub=1;gm=3;gb=1;rf=1;minle=346;wt=20:21:77:117:119:96:103:170:32;wtv=2.6373:1.2115:1.1952:1.5543:1.4658:1.5130:1.0993:1.3631:5.0913;) and [GuildOx](http://www.guildox.com/wr.asp?usr=&ser=&grp=www&Cla=1024&F=H&Int=3.2213&Spi=2.2387&spd=2.4038&mhit=2.2286&mcr=0.9007&mh=1.7434&Mr=1.1686&Ver=6) for items comparison, or a string to paste in [Pawn](http://wow.curse.com/downloads/wow-addons/details/pawn.aspx). Simulationcraft can also export CSV and XML files for your custom tools, or combat logs in a custom format.

> Finally, the [Elitist Jerks forums](http://elitistjerks.com/forums.php) and others theorycrafters' lairs are frequently monitored to grab the latest bis lists and discoveries, and their feedback about Simulationcraft.

> ![http://www.simulationcraft.org/images/wiki/chardev_top.jpg](http://www.simulationcraft.org/images/wiki/chardev_top.jpg)

# Have your simulated avatar play the way you want
> Do you want to test out another dps rotation? Check whether you should pop your cooldowns as soon as possible or try to synchronize them with bloodlust/heroism or a certain phase of the combat? You can do it, check out the documentation (see [ActionLists](ActionLists)). Here is a sample actions list:
```
 actions+=/slice_and_dice,if=buff.slice_and_dice.down&time<4
 actions+=/slice_and_dice,if=buff.slice_and_dice.remains<2&combo_points>=3
 actions+=/killing_spree,if=energy<20&buff.slice_and_dice.remains>5
 actions+=/rupture,if=!ticking&combo_points=5&target.time_to_die>10
 actions+=/eviscerate,if=combo_points=5&buff.slice_and_dice.remains>7&dot.rupture.remains>6
 actions+=/eviscerate,if=combo_points>=4&buff.slice_and_dice.remains>4&energy>40&dot.rupture.remains>5
 actions+=/eviscerate,if=combo_points=5&target.time_to_die<10
 actions+=/revealing_strike,if=combo_points=4&buff.slice_and_dice.remains>8
 actions+=/sinister_strike,if=combo_points<5
 actions+=/adrenaline_rush,if=energy<20
```

# Simulate real conditions
> Do most fights look like a tank's n spank? No. Sometimes there are adds spawning, sometimes you suffer heavy damages, sometimes the boss may take twice much more damages, sometimes he become invulnerable, sometimes you have to kick his incantation, sometimes you have to move, sometimes you are distracted by what's happening on your screen, etc... Simulationcraft can simulate that.
```
 # This is currently not functioning as we transition to true multi-target support.
```
> Besides, Simulationcraft offers you tools to simulate human behaviours: your players may have a high latency, they may have brain lag and take time to notice a spell miss or a new buff/debuff, they may do mistakes and hit the wrong button.

# Internationalization
> Simulationcraft is only available in English. However, it can work with all versions of the wow armory and battle.net websites (notably: Russian, Chinese, Korean and Taiwanese characters and guilds can be imported). If you use the command-line client, your files must be encoded as latin1 or utf-8, please take time to read [TextualConfigurationInterface#Characters\_encoding](TextualConfigurationInterface#Characters_encoding).

# Limitations
> At first, Simulationcraft was made for damage dealers, with just a dummy target. It evolved since then but there are still some limitations although we hope to see some of them be removed throughout the course of 2011.

  * **Tanking:** currently, you can be put in the front of the target and have it hit you and do damages to you but, aside from rage generation and damage-based procs, it's pretty useless. Simulationcraft will only display your dps, not your tps (threat per second) and there is absolutely no data regarding mitigation. There is no aggro support also.

  * **Healing:** it has been recently introduced but is only available for priests (discipline or holy) so far. It is also rudimentary yet: you will only heal the tank or yourself. Finally, the hps will be displayed as "dps", you can't have stats for both at the same time. See [Priest\_Healing\_Module](Priest_Healing_Module).

  * **Many targets:** currently, you can have adds (either periodically spawning adds who will despawn after some time, or adds remaining for the whole fight, as long as the main target is alive). Those adds are mere dummy targets: their health pools do not matter, they do not hit anyone, etc... Besides, actions lists only have a limited support: you can choose spells based on the numbers of available target but there is no support for multi-dotting classes. Finally, only cleave-like spells work, not genuine aoe.