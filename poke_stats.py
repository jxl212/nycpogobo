from collections import *
import os, re, queue
from datetime import datetime
from termcolor import cprint, colored


class PokeStats:
    def __init__(self):
        self.pokemons = defaultdict(queue.Queue)

    def update(self, pokemon_name):
        cur_time=datetime.now()
        self.pokemons[pokemon_name].put(cur_time)
        self.remove_old_entries(pokemon_name)

    def spawn_per_hour(self,pokemon_name):
        size=self.pokemons[pokemon_name].qsize()
        return int(size)

    def remove_old_entries(self,pokemon_name,max_sec=int(60*60)):
        cur_time=datetime.now()
        for data_point in self.pokemons[pokemon_name].queue:
            t_sec=(cur_time - data_point)
            if t_sec.total_seconds() < max_sec:
                return
            self.pokemons[pokemon_name].queue.popleft()


pokestats=PokeStats()