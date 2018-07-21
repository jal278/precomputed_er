# Copyright (c) 2017 Joel Lehman
# Copyright (c) 2018 Uber Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from precomputed_domain import *
import math
from pdb import set_trace as bb

#general search class 
MAX_ARCHIVE_SIZE = 1000
class search:

 def __init__(self,domain,pop_size=250,tourn_size=2,elites=1,drift=0.0,fuss=False,mutation_rate=0.8,diversity=0.0,search_mode="fitness",log_evolvability=False):

  self.epoch_count = 0
  self.domain = domain
  self.population = [self.domain.generate_random() for _ in xrange(pop_size)]
  self.pop_size = pop_size
  self.tourn_size = tourn_size 
  self.elites = elites
  self.diversity_pressure = diversity
  self.log_evolvability = log_evolvability

  self.behavior_count=np.zeros(10000) #for counting how many behaviors have been encountered
  
  self.rarity=False
  self.novelty=False
  self.fuss=False
  self.evolvability=False
  self.evo_everywhere=False
  self.evo_steps=1

  #instrument search through metrics class in precomputed_domain.py
  self.metrics = metrics(domain)

  #what search heuristic to use
  if search_mode=='fitness':
   pass
  if search_mode=='rarity':
   self.rarity=True
  if search_mode=='novelty':
    self.novelty=True
  if search_mode=='fuss':
   self.fuss=True
  if search_mode.count('evolvability')>0:
   self.evolvability=True
   if search_mode.count('everywhere')>0:
       self.evo_everywhere=True
   else:
       self.evo_steps=int(search_mode[-1])

  #evaluations spent and solved flag
  self.evals=0
  self.solved=False

  #novelty search specific
  self.archive = np.zeros((MAX_ARCHIVE_SIZE,domain.behavior_size))
  self.archive_size = 0 
  self.archive_ptr = 0

  self.map_evolvability = lambda x:self.map_general(self.domain.evolvability_everywhere,x)
  self.map_fitness = lambda x,y:self.domain.map_fitness(x)

  if self.evolvability:
   if self.evo_everywhere:
       self.domain.everywhere_evolvability_calculate()
       self.map_fitness = lambda x,y:self.map_general(self.domain.evolvability_everywhere,x)
   else:
       self.domain.kstep_evolvability_calculate(self.evo_steps)
       self.map_fitness = lambda x,y:self.map_general(lambda ind:self.domain.evolvability_ks(ind,k=self.evo_steps),x)

  if self.rarity:
   self.map_fitness = lambda x,y:self.map_general(self.metrics.rarity_score,x)
  if self.novelty:
   self.map_fitness = lambda x,y:self.domain.map_novelty(x,y)

  #ground-truth fitness (i.e. prespecified domain fitness)
  self.map_gt_fitness = lambda x,y:self.domain.map_fitness(x)

  self.mutation_rate = mutation_rate
  self.drift = drift
  self.best_gt = -1e10

  #fitness uniform selection and tournament selection 
  if self.fuss:
      self.selection_mechanism = lambda x:self.select_fuss(x)
  else:
      self.selection_mechanism = lambda x:self.select_tourn(x)

  self.fitness = self.map_fitness(self.population,self.archive[:self.archive_size])
  if log_evolvability:
   self.evolvability = self.map_evolvability(self.population)

 #map some metric over the population
 def map_general(self,measure,population):
      return np.array([measure(x) for x in population])

 #fitness uniform selection
 def select_fuss(self,pop):
     rnd_fit = random.uniform(self.min_fit,self.max_fit)
     abs_dif = self.fitness - rnd_fit
     closest_idx = np.argmin(abs_dif)
     if random.random()<self.drift:
        closest_idx = random.randint(0,self.pop_size-1)

     return self.domain.clone(pop[closest_idx])

 #tournament selection
 def select_tourn(self,pop):
   offs = np.random.randint(0,self.pop_size,self.tourn_size)
   fits = self.fitness[offs]
   if random.random()<self.drift:
       off = random.randint(0,self.pop_size-1)
   else:
       off = offs[np.argmax(fits)]
   return self.domain.clone(pop[off])

 #create new population
 def select(self,pop):
  elites=self.elites
  champ_idx = np.argmax(self.fitness)
  newpop = []

  #elitism
  for _ in xrange(elites):
   newpop.append(self.domain.clone(pop[champ_idx]))
 
  #store min and max fitness 
  self.min_fit = self.fitness.min()
  self.max_fit = self.fitness.max()

  #rest of population is offspring from previous pop
  for _ in xrange(self.pop_size-elites):
   child = self.selection_mechanism(pop)

   if random.random()<self.mutation_rate:
    child = self.domain.mutate(child) 

   newpop.append(child)

  return newpop

 #simple hill-climbing method
 def hillclimb(self,eval_budget,shadow=False):
  champ = self.population[0]
  champ_fitness = self.map_fitness([champ],None)[0]
  orig_fitness = champ_fitness
  selections = 0
  solved=False

  for _ in xrange(eval_budget):
   offspring = self.domain.clone(champ)
   offspring = self.domain.mutate(offspring)

   offspring_fitness = self.map_fitness([offspring],None)[0]
   solution = self.domain.map_solution([offspring])[0]
   if shadow:
       champ=offspring

   if solution:
       print "solved"
       solved=True

   if offspring_fitness > champ_fitness:
       champ_fitness = offspring_fitness
       champ = offspring
       print _,champ_fitness
       selections+=1

  return orig_fitness,champ_fitness,selections,solved

 #do one epoch of evolution  
 def epoch(self,count_behaviors=True):
  self.epoch_count+=1
  self.evals+=self.pop_size
  new_population = self.select(self.population)

  #add one individual to archive each epoch for NS
  for _ in xrange(1):
   if self.archive_ptr>=MAX_ARCHIVE_SIZE:
    self.archive_ptr = self.archive_ptr % MAX_ARCHIVE_SIZE
   self.archive[self.archive_ptr] = self.domain.map_behavior([random.choice(self.population)])[0]

   if self.archive_size<MAX_ARCHIVE_SIZE:
    self.archive_size+=1

   self.archive_ptr+=1
   
  self.population = new_population
  self.fitness = self.map_fitness(self.population,self.archive[:self.archive_size]) 
  self.gt_fitness = self.map_gt_fitness(self.population,None)
  #self.evolvability = self.map_evolvability(self.population)
  self.solutions = self.domain.map_solution(self.population)

  if count_behaviors:
   self.behaviorhash = self.domain.map_behaviorhash(self.population)
   np.add.at(self.behavior_count,self.behaviorhash,1)

  if (self.solutions.sum()>0):
   champ = np.argmax(self.solutions)
   #print self.gt_fitness[np.argmax(self.solutions)]
   self.solved=True
   return True 

  #print self.evolvability.max(),self.evolvability.mean(),self.evolvability.min() 
  
  #keep track of overall best fitnes individual
  if self.best_gt < self.gt_fitness.max():
   self.best_gt = self.gt_fitness.max()
   print self.epoch_count,self.best_gt

def repeat_search_rarity(generator,times,seeds=None,gens=250):
 solved=[]
 evals=[]
 data=np.zeros((times,gens))
 if seeds==None:
     seeds=range(1,times+1)
 for x in range(times):
  set_seeds(seeds[x])
  search=generator()

  for _ in xrange(gens):
   if _%100==0:
    print _*search.pop_size
   sol = search.epoch()
   #if sol:
   # print "solved" 
   # break
   rarity= np.array(search.map_general(search.metrics.rarity_score,search.population))
   data[x,_] = rarity.max() 
  print search.solved
  if search.solved:
      solved.append(True)
      evals.append(search.evals)
  else:
      solved.append(False)
      evals.append(-1)
 return data

def repeat_search_evolvability(generator,times,seeds=None,gens=250):
 solved=[]
 evals=[]
 data=np.zeros((times,gens))
 if seeds==None:
     seeds=range(1,times+1)
 for x in range(times):
  set_seeds(seeds[x])
  search=generator()

  for _ in xrange(gens):
   if _%100==0:
    print _*search.pop_size
   sol = search.epoch()
   #if sol:
   # print "solved" 
   # break
   evolvability = np.array(search.map_general(lambda ind:search.domain.evolvability_everywhere(ind),search.population))
   data[x,_] = evolvability.max() 
  print search.solved
  if search.solved:
      solved.append(True)
      evals.append(search.evals)
  else:
      solved.append(False)
      evals.append(-1)
 return data


def repeat_search_count_behaviors(generator,times,seeds=None,gens=250):
 solved=[]
 evals=[]
 total_behaviors=np.zeros((times,gens))
 if seeds==None:
     seeds=range(1,times+1)
 for x in range(times):
  set_seeds(seeds[x])
  search=generator()

  for _ in xrange(gens):
   if _%100==0:
    print _*search.pop_size
   sol = search.epoch()
   #if sol:
   # print "solved" 
   # break
   total_behaviors[x,_] = (search.behavior_count>0).sum() 
  print search.solved
  if search.solved:
      solved.append(True)
      evals.append(search.evals)
  else:
      solved.append(False)
      evals.append(-1)
 return total_behaviors

def repeat_search(generator,times,seeds=None,gens=250):
 solved=[]
 evals=[]
 if seeds==None:
     seeds=range(1,times+1)
 for x in range(times):
  set_seeds(seeds[x])
  search=generator()

  for _ in xrange(gens):
   if _%100==0:
    print _*search.pop_size
   sol = search.epoch()
   if sol:
    print "solved" 
    break
  print search.solved
  if search.solved:
      solved.append(True)
      evals.append(search.evals)
  else:
      solved.append(False)
      evals.append(-1)
 return solved,evals

