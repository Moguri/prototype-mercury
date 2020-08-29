Game Design Document
====================

Intro
-----

You are a Golem Master and you want to be the best there ever was.
So, grab some Golems, raise them big and strong, and do battle with other Golem Masters in a tactical combat system.

This game is inspired by:

* Final Fantasy Tactics (combat, stats, jobs)
* Final Fantasy Tactics Advanced (different job trees for different races)
* Monster Rancher (monster raising sim)

Gameplay Description
--------------------

Jobs
^^^^

This game utilizes a "job system."
Each monster has access to a set of jobs and has a currently active job.
Different jobs can provide different stat boosts and access to certain abilities.
Jobs can also have requirements that must be met before they can be used (e.g., a certain number of levels in another job).

A monster gains "experience" in a job via "Job Points" (or JP).
After acquiring enough JP, a monster will obtain a new level in the current job.
This is no limit to the number of levels that can be acquired for a job.
However, job levels have no benefits themselves (e.g., stat gains).
Instead, job levels can used to unlock new classes, and the JP earned can be spent on purchasing new :ref:`abilities`.
Jobs can also have a number of stat boosts available for purchase with JP.

Details on all available jobs can be found :doc:`here <_gen/jobs>`.

Tags
^^^^

Various requirements in the game are determined by "tags."
Some examples of requirements include:

* what jobs a Golem has access to
* what breeds a trainer has access to

Monsters and trainers each have a pool of tags.
To determine eligibility the item being checked for (e.g., a job) is compared to the appropriate tag pool.
If all tags on the item are present in the tag pool, the requirements are met.
In other words, the required tags are an "all of" relationship.

A trainer's tag pool contains:

* Any "personal tags" acquired

A monster's tag pool contains:

* The trainer's tags
* The breed's tags
* A tag for each item in a Cartesian product of available jobs and their levels.
  For example, a monster with three levels in :ref:`job-squire` and two levels in :ref:`job-ruinsmith` will have the following tags:

   * ``job_squire_1``
   * ``job_squire_2``
   * ``job_squire_3``
   * ``job_ruinsmith_1``
   * ``job_ruinsmith_2``

Monster Stats
^^^^^^^^^^^^^

The monster stats are:

Hit Points
   The amount of damage a monster can take before going down

Magic Points
   A resource for using abilities

Physical Attack
   Multiplier for damage on ``physical`` abilities

Magical Attack
   Multiplier for damage on ``magical`` abilities

Movement
   The number of tiles the monster can move in a single turn

.. _abilities:

Abilities
^^^^^^^^^

Monsters have access to a set of abilities.
By default, all monsters have a "Basic Attack" as determined by their active job.
In addition to this "Basic Attack," monsters have purchased abilities.
Abilities can be purchased for the active job with JP earned while that job has been active.
Different jobs have access to different abilities.

Once an ability has been purchased, the monster will continue to have access to it even when changing jobs.
This can lead to some fun and interesting monster builds.

Abilities have the following stats:

MP Cost
   How much MP is required to use this ability (can be zero)

JP Cost
   How much JP is required to purchase this ability

Type
   Either ``physical`` or ``magical``

Range (min and max)
   The number of tiles away the ability target can be from the ability user

Power
   This ability power (AP) determines how strong ability effects (e.g., damage) are

Hit Chance:
   How likely the ability is to succeed (100% is common)

In addition to stats, abilities have a list of "effects" such as:

* Doing damage (or healing with negative damage)
* Moving the ability user
* Moving the ability target
* Displaying visual effects
* Playing a sound effect

Some effects (e.g., damage) make use of a derived "strength" stat.
This is the ability power (AP) multiplied by one of physical attack (PA) or magical attack (MA) depending on the ability type.
For example the damage of a magical attack would be ``AP * MA``.

Combat
^^^^^^

This is the current focus of the game.
The combat is turn-based.
On each monster's turn, a monster may move up to their ``movement`` stat and use an ability (in any order).
Movement can also be split before and after using an ability.

Combat ends when one side no longer has any monsters above zero hit points.

Golem Acquisition
^^^^^^^^^^^^^^^^^

Monsters are currently acquired for free from the "Market."
This will be expanded on in the future (see :ref:`additional_ideas`).

Golem Raising
^^^^^^^^^^^^^

This is pretty undefined at the moment (see :ref:`additional_ideas`).

Artistic Style Outline
----------------------

* Simple
* Clean
* Bright/vivid colors
* NPR/Stylized

Systematic Breakdown of Components
----------------------------------

* Panda3D (often shortened to Panda) is the game engine being used
* PBR rendering with IBL

  * Using panda3d-simplepbr, still need to add IBL

* GUI

   * Currently using CEF, which is rather overkill

      * Keeps us stuck on Python 3.7
      * Dynamically links against Python, which causes problems to work around
      * 100+MB dependency
      * Can be laggy and resource intensive
      * As a pro, it allows us to use popular web front-end technologies and CSS animations look nice

   * Mostly need to drive some menus, so DirectGUI (built-in Panda GUI library) may be sufficient

* Game Data

   * Stored in JSON files and managed by ``gamedb``

* Data Editor

   * It is desirable to not require hand-editing of JSON files
   * Ideally done with web technologies and JSON Editor
   * Can use a web server (built using Flask, bottle, etc.) that we point a web browser to over ``localhost``
   * Proof-of-concept Started in ``editor`` branch

* Abilities system

   * A system to easily define and execute abilities

* Visual Effects

   * Need VFX for abilities
   * Will start with Panda's built-in particle effects
   * Will need to use a custom file format since ptf relies on ``eval()``, which is bad news

* Audio

   * Need both background music and sound effects
   * This can be handled by Pandaand its built-in OpenAL support
   * Do we want to try something with adaptive audio?

* Save/Load

   * This game requires saving and loading
   * Should be able to dump/restore state from JSON data (most internal data already has JSON representations)

Suggested Game Flow Diagram
---------------------------

The main game loop is to participate in combats to gain resources to upgrade monsters.
Once the player completes the "final battle," they "win" the game, but they may continue to play.

.. mermaid::

   graph TD
      get_trainer(Create/Load Trainer) --> ranch{Ranch}
      ranch -->get_monster(Get Monster from Market)
      get_monster --> ranch
      ranch --> review_monsters(Review/Upgrade Monsters)
      review_monsters --> ranch
      ranch --> combat
      combat --> gain_jp(Gain JP)
      gain_jp --> ranch
      ranch --> boss(Boss Fight)
      boss --> end_game[End Game]

.. _additional_ideas:

Additional Ideas and Possibilities
----------------------------------

* Monster age and death

   * Have set lifespans with events that can reduce the lifespan (e.g., losing combat, stress)
   * Monsters behave differently depending on age?

* Acquire monster "cores" or "fragments" upon monster death to improve newly created monsters
* Player funds

   * Need ways to earn (winning combat/tournaments)
   * Need costs

      * Rent?
      * Monster upkeep?
      * Buying monsters or items?

* Non-combat ways to improve monsters and/or acquire funds?
* Items

   * One or two "accessory" slots on monsters to give bonuses
   * Make non-visible to reduce the amount of art required
   * Consumables?

* Allow more ratios of PA and MA in abilities

   * Currently 100% PA or 100% MA
   * For example: 50% PA and 50% MA
   * May just do "mixed" type of 50/50 instead of exposing a ratio

* Control how many monsters a trainer can take into combat with some sort of spirit points (SP)

   * The trainer would have a limit (one that could be increased) of SP to spend building a team
   * Monsters would have different SP costs (with possible discounts)

* Some sort of skill tree or perks for trainers?
