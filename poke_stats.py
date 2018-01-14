from collections import *
import os, re, queue
from datetime import datetime
from termcolor import cprint, colored


class PokeStats:
    def __init__(self):
        self.pokemons = defaultdict(queue.Queue)

    def update(self, pokemon_name):
        cur_time=datetime.now()
        self.pokemons[pokemon_name].queue.append(cur_time)
        while (not self.pokemons[pokemon_name].empty()) and \
            (((cur_time - self.pokemons[pokemon_name].queue[0]).total_seconds() // 3600) >  0):
            self.pokemons[pokemon_name].queue.popleft()

    def spawn_per_hour(self,pokemon_name):
        size=self.pokemons[pokemon_name].qsize()
        return int(size)


pokestats=PokeStats()
