from precompute_search import *

if __name__=='__main__': 

 maze = 'medium'
 search_type = 'rarity'
 
 domain = precomputed_maze_domain(maze,storage_directory="logs/",mmap=True)

 rarity = lambda : search(domain,search_mode="rarity",pop_size=500,tourn_size=2)
 evo1 = lambda : search(domain,search_mode="evolvability1",pop_size=500)
 evo2 = lambda : search(domain,search_mode="evolvability2",pop_size=500)
 evo3 = lambda : search(domain,search_mode="evolvability3",pop_size=500)
 evo4 = lambda : search(domain,search_mode="evolvability4",pop_size=500)
 evo_ev = lambda : search(domain,search_mode='evolvability_everywhere',pop_size=500)

 nov = lambda : search(domain,search_mode="novelty",tourn_size=2,pop_size=500) #was 0.25
 fit = lambda : search(domain,tourn_size=2,pop_size=500)
 rnd = lambda : search(domain,tourn_size=3,pop_size=500,drift=1.0,elites=0)

 searches = {'rarity':rarity,'evo1':evo1,'evo2':evo2,'evo3':evo3,'evo_ev':evo_ev,'nov':nov,'fit':fit,'rnd':rnd}
  
 search = searches[search_type]

 for _ in xrange(1000):
  if _%100==0:
   print _*search.pop_size
  sol = search.epoch()
  if sol:
    print "solved" 
    break
  if(disp):
    render(search,domain)

 #how many evals did it take to solve?
 print search.evals
