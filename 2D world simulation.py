import numpy as np
import matplotlib as mpl# type: ignore
import matplotlib.pyplot as plt # type: ignore
#import scipy
import math
import pygame
from astropy import constants, units # type: ignore
import copy
import typing


YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
DEFAULTSCALE = 39/constants.au #pixels per AU
COORDINATE = typing.Tuple[int, int]
PANNING_VELOCITY = 5
BACKGROUND_COLOR = BLACK
ZOOM = 1.1
TIMESTEP =  3600*24 #the game will be sped up by this number (1 day per second)

pygame.init()
font = pygame.font.Font(None, 32)
#L_sun solar luminosity
#pygame.image.load('bg.jpg') loads image to background

RGB = typing.Tuple[int, int, int]

def planetSim():

	WIDTH, HEIGHT = 1250, 500
	CENTER = (WIDTH/2, HEIGHT/2)

	class Planet_group(pygame.sprite.Group):
		
		def __init__(self):
			super().__init__()
			self.offset = pygame.math.Vector2() #for the camera panning; no arguments means (0,0) coordinates
			self.scale = DEFAULTSCALE
			self.radiusToScale:bool = False #type:ignore
		
		auToPixels = lambda self, actualDimension: (actualDimension * self.scale).value
		#takes the actual position of celestial body and converts it to pixels

		def centralize(self):
			"""Resets the position of each planet in the group and zoom_scale""" #this is a docstring
			self.scale = DEFAULTSCALE
			self.offset *= 0
	
		def draw(self, surface): #overrides Group's draw method
			for planet in self.sprites():
				planet.rect.center = (self.auToPixels(planet.actual_pos[0]), self.auToPixels(planet.actual_pos[1]) + HEIGHT/2)
				surface.blit(planet.image, planet.rect.topleft + self.offset)
		
		def toggleRadius(self): #toggle the radii to scale or to display
			self.radiusToScale = not self.radiusToScale
			for planet in self.sprites():
				if self.radiusToScale:
					planet.image.fill(BACKGROUND_COLOR)
					pygame.draw.circle(planet.image, planet.color, (self.auToPixels(planet.actualRadius), self.auToPixels(planet.actualRadius)), self.auToPixels(planet.actualRadius))
				else:
					planet.image.fill(BACKGROUND_COLOR)
					pygame.draw.circle(planet.image, planet.color, (planet.displayRadius, planet.displayRadius), planet.displayRadius)

	class Body(pygame.sprite.Sprite):
		
		def __init__(self, *groups, width:int, height:int, pos:COORDINATE, mass, color:RGB = (255,255,255), velocity:units.m / units.s = 0 * units.m / units.s):
			super().__init__(*groups)
			self.image = pygame.Surface((width*2, height*2)) 
			self.image.set_colorkey(BLACK) #removes black edges from the planet
			self.rect:pygame.rect.Rect = self.image.get_rect()
			self.initialPos = pos
			self.pos = pos
	
		'''def reset(self):
			self.rect.center = self.initialPos'''
		

	class CelestialBody(Body):

		def __init__(self, planet_group:Planet_group, displayRadius:int, color:RGB, mass:units.kg, actualRadius:units.m, distance_to_sun = 0 * units.m): #constructor: the init() function
			super().__init__(planet_group, width = displayRadius, height = displayRadius, pos = (0,HEIGHT/2), mass = mass, color = color) #no need to pass in self for super()
			"""self.d = 0 * units.m#distance from sun to sun = 0
			
			self.scale = DEFAULTSCALE # in unitless pixels per au
			self.actualX = 0 * units.m#x position; only changes with orbits
			self.actualY = 0 * units.m"""
			self.scale = DEFAULTSCALE
			pygame.draw.circle(self.image, color, (displayRadius, displayRadius), displayRadius) #type:ignore
			self.displayRadius = displayRadius
			self.actualRadius = actualRadius.to(units.m)
			self.color:RGB = color
			self.mass = mass
			self.distance_to_sun =  distance_to_sun #initial/average distance to the sun
			self.actual_pos:COORDINATE = (distance_to_sun, 0 * units.m)
		
		#def scale(self, scale): scales all 
					
		"""def draw(self):
			pygame.draw.circle(self.image, self.color, (self.screenX, self.screenY), self.r)"""

		"""	def increaseScale(self, cursorX = 0, cursorY = HEIGHT/2):
			planetScale = self.scale * 1.1 #1.1 is an arbitrary increase of the scale
			if planetScale * constants.au < 20000000:
				self.scale = planetScale
				self.screenX = self.auToPixels(self.actualX)
				self.screenY = self.auToPixels(self.actualY) + HEIGHT/2
				

		def decreaseScale(self, cursorX = 0, cursorY = HEIGHT/2):
			planetScale = self.scale / 1.1
			if planetScale * constants.au > 0.5:
				self.scale = planetScale
				self.screenX = self.auToPixels(self.actualX)
				self.screenY = self.auToPixels(self.actualY) + HEIGHT/2


		def increaseRadius(self):
			planetR = self.r * 1.1
			if planetR < HEIGHT/4: #this HEIGHT/4 was arbitrarily chosen.
				self.r = planetR
				self.radiusToScale = False

		def decreaseRadius(self):
			planetR = self.r / 1.1
			if planetR >= 1:
				self.r = planetR
				self.radiusToScale = False"""





			#super().__init__(self, displayRadius, color, m, actualRadius) #another way to do the same thing as the line above?.
			 #distance from the sun; doesn't change with camera movement
			#self.actualX = self.d.copy()
			#self.screenX = self.auToPixels(self.actualX)

	"""	def calcForceGravity(self, otherCelestialBody):
			d_x = otherCelestialBody.x - self.x #distance between two bodies in m; negative distances will be squared
			d_y = otherCelestialBody.y -self.y
			d = math.sqrt(d_x**2 + d_y**2)
			if otherCelestialBody.d == 0: #if otherCelestialBody is the sun
				self.d = d

			f = constants.G * self.mass* otherCelestialBody.mass/ d**2
			theta = math.atan2(d_y, d_x)
			f_x = f * math.cos(theta)
			f_y = f * math.sin(theta)
			return f_x, f_y"""


	run = True
	clock = pygame.time.Clock() #otherwise, the game runs at the speed of the processor
	screenPlanets = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Planet simulation")

	planet_group = Planet_group()
	sun = CelestialBody(planet_group, 30, YELLOW, constants.M_sun, constants.R_sun)
	mercury = CelestialBody(planet_group, 1, (100,100,100), 0.33e4*units.kg, 4879/2*units.km, 57.9e9*units.m)
	venus = CelestialBody(planet_group, 3, YELLOW, 4.87e4*units.kg, 12104/2*units.km, 108.2e9*units.m,)
	earth = CelestialBody(planet_group, 3, BLUE, constants.M_earth, constants.R_earth, (1*units.au).to(units.m))
	mars = CelestialBody(planet_group, 2, RED, 0.642e24*units.kg,6792/2*units.km, 228e9*units.m)
	jupiter = CelestialBody(planet_group, 35, (120,40, 0), constants.M_jup, constants.R_jup, 778.5e9*units.m)
	saturn = CelestialBody(planet_group, 30, (255,255,102), 568e24*units.kg, 120536/2*units.km, 1432e9*units.m)
	uranus = CelestialBody(planet_group, 14, (0, 120, 125), 86.8e24*units.kg, 51118/2*units.km, 2867e9*units.m)
	neptune = CelestialBody(planet_group, 13, BLUE, 102e24*units.kg, 49528/2*units.km, 4515e9*units.m)

	while run:
		clock.tick(60)	
		cursorX = pygame.mouse.get_pos()[0]
		cursorY = pygame.mouse.get_pos()[1]
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
			if event.type == pygame.KEYDOWN:
		
				""" if event.key == pygame.K_j:
					centralizeOnPlanet(earth, planets) """
				if event.key == pygame.K_z:
					planet_group.toggleRadius()
				if event.key == pygame.K_c:
					planet_group.centralize()
			
			if event.type == pygame.MOUSEWHEEL: #pygame.MOUSEBUTTONDOWN
				#print(event.y)
				if event.y > 0:
					planet_group.scale *= event.y
					
		userInput = pygame.key.get_pressed()
		
		if userInput[pygame.K_KP_PLUS]:
			planet_group.scale *= ZOOM
		
		elif userInput[pygame.K_KP_MINUS]:
			planet_group.scale /= ZOOM
		
		if userInput[pygame.K_RIGHT]:
			planet_group.offset.x -= PANNING_VELOCITY
		
		elif userInput[pygame.K_LEFT]:
			planet_group.offset.x += PANNING_VELOCITY
		
		if userInput[pygame.K_UP]:
			planet_group.offset.y += PANNING_VELOCITY
		
		elif userInput[pygame.K_DOWN]:
			planet_group.offset.y -= PANNING_VELOCITY
			
		"""	if userInput[pygame.K_r]:
				planet.increaseRadius()
			
			elif userInput[pygame.K_e]:
				planet.decreaseRadius()"""
		screenPlanets.fill(BACKGROUND_COLOR)
		planet_group.draw(screenPlanets)
		"""	auPerPixel = round(((1*units.au).to(units.m)/planets.sprites()[0].scale).value, 2) #How many aus a pixel represents
		scaleTxt = font.render("Scale: 1 pixel =  {:e}m".format(auPerPixel), True, (255,255,255))
		screenPlanets.blit(scaleTxt, (10, HEIGHT - 30)) #prints the scale on the pygame screen
		
		if planet_group.sprites()[0].radiusToScale:
			radiiToScaleStr = "Radii and distances to scale."
		else:
			radiiToScaleStr = "Radii not to scale, but distances to scale."
		screenPlanets.blit(font.render(radiiToScaleStr, True, (255,255,255)), (10, HEIGHT - 60))"""
		pygame.display.flip()

	pygame.quit()

#print(constants.G.value)
#print(constants.au)
planetSim()
#print(constants.M_sun)