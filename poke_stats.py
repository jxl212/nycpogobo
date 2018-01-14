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
        first=self.pokemons[pokemon_name].queue[0]
        last=self.pokemons[pokemon_name].queue[-1]
        delta=last-first
        if delta.total_seconds() == 0:
            return {"per_hour":None, "per_minute":None, "per_second":None}
        per_second=int(size) / delta.total_seconds()
        per_minute=int(size) / (delta.total_seconds() / 60)
        per_hour=int(size) / (delta.total_seconds() / 3600)
        return {"per_hour":int(per_hour * 1000)/1000, "per_minute":int(per_minute * 1000)/1000, "per_second":int(per_second * 1000)/1000}

    def remove_old_entries(self,pokemon_name,max_sec=int(60*60)):
        cur_time=datetime.now()
        for data_point in self.pokemons[pokemon_name].queue:
            t_sec=(cur_time - data_point)
            if t_sec.total_seconds() < max_sec:
                return
            self.pokemons[pokemon_name].queue.popleft()


pokestats=PokeStats()
