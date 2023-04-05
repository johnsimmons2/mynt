# How To
- See the demo project apricot-dp.
- Modify the apricot-dp.mynt.json file
- Coming soon: Mynt lang to program directly into minecraft commands. Example code:

### apricot-dp.mynt
```cpp
// This is a comment

// These are variables, denoted with #.
// this one line creates a scoreboard that increases as
//  a player holds right mouse down.
score #magictest = 0 | minecraft.used:minecraft.carrot_on_a_stick
// All minecraft entities will be valid primitive types, load the 
//  nbt data and properties via any supplied json file in /assets/.
zombie #gruntzombie = './mobs/grunt.json'

// You can set arbitrary variables and reference them anywhere.
number #g10 = 10
number #g500 = 500

// You can reference this variable in './mobs/grunt.json' or elsewhere.
number #baseZombieHealth = 40

// Requires a main and a load as well as functions to compile.
main {
    // Runs every frame
}

load {
    // Runs once on load or reload. Any variables declared above will
    //  automatically be initialized as needed.

    // The next line is optional, otherwise will use the name of the file.
    $name apricot-dp
    // Required, or else it will make for an ugly description.
    $description Apricot: Data-Pack demo
}

// Optional tag to initialize or modify events.
events {
}

functions = [
    // Functions are composed like:
    //      "name { body } <if | $EVENT> <{ condition }>"

    // This function shouts "fire", resets the counter,
    //  and then fires the timer off... but only when
    //  the condition that the given player has a required score.
    holdClickToFire {
        $say @a Fire!
        $set #magictest 0
        $start #test-timer2 after 2s
    } if {
        $score @a #magictest >= 20
    },

    // This creates a function that tells everyone on the server 
    //  that somebody slept in a bed, so long that the event $sleep
    //  was triggered.
    sleepShout {
        $say @a somebody slept!
    } $sleep

    test-timer {
        $say $blue $bold @a Summoning stick used...
        $summon creeper
        $summon #GruntZombie at @a
    }
]
```

## Benefits to Mynt?
No clue, but it is fun to make and it completely takes out the issue of having to structure and navigate dozens of folders and commands...