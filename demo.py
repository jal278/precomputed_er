from precompute_search import *

#render function
def render(search,domain,screen,background):
 pop = search.population
 novelty = search.novelty
 archive = search.archive

 #erase screen
 screen.blit(background, (0, 0))

 #for scaling color (which indicates performance)
 mn_fit = search.fitness.min()
 mx_fit = search.fitness.max()

 SZX,SZY = screen.get_size()

 for idx,robot in enumerate(pop):
  x,y = domain.norm_behavior(robot)
  
  #convert to screen coords
  x=x*SZX
  y=y*SZY
  rect=(int(x),int(y),5,5)

  #calculate color based on performance
  col = (search.fitness[idx]-mn_fit)/(mx_fit-mn_fit)*255.0
  col = int(col)

  #draw to screen
  pygame.draw.rect(screen,col,rect,0)

 #if doing novelty search, also draw archive
 if novelty:
  for robot in archive:
   x,y = robot/300
   x=x*SZX
   y=y*SZY
   rect=(int(x),int(y),5,5)
   pygame.draw.rect(screen,(0,255,0),rect,0)

 pygame.display.flip()



if __name__=='__main__': 
 maze = 'medium'
 search_type = 'fit'

 #render flag
 disp=True

 #display depends upon pygame
 if disp:
  #window size in pixels
  SZX=SZY=400
  import pygame
  from pygame.locals import *
  pygame.init()
  pygame.display.set_caption('Viz')
  screen =pygame.display.set_mode((SZX,SZY))
 
  background = pygame.Surface(screen.get_size())
  background = background.convert()
  background.fill((250, 250, 250,255))


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
  
 if search_type not in searches:
   print 'available search types:',searches.keys() 

 search = searches[search_type]()

 for _ in xrange(1000):
  if _%100==0:
   print search.pop_size

  #is the maze solved?
  sol = search.epoch()

  if sol:
    print "solved" 
    break
  if(disp):
    render(search,domain,screen,background)

 #how many evals did it take to solve?
 print search.evals
