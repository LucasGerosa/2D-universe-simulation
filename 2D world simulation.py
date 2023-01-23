import numpy as np
#import matplotlib
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
m_per_s = units.m / units.s
PANNING_VELOCITY = 5
BACKGROUND_COLOR = BLACK
ZOOM = 1.1 #the increment of the zoom
TIMESTEP =  3600*24 #the game will be sped up by this number (1 day per second)


pygame.init()
font = pygame.font.Font(None, 32)
#L_sun solar luminosity
#pygame.image.load('bg.jpg') loads image to background

RGB = typing.Tuple[int, int, int]


WIDTH, HEIGHT = 1250, 600
CENTER = (WIDTH/2, HEIGHT/2)
SCREEN_BORDERS = {'left': WIDTH//7, 'right': WIDTH//7, 'top': HEIGHT//7, 'bottom': HEIGHT//7}

def create_array(u = None, values = (0,0)): #returns a numpy array from coordinates and a unit. The unit can be specified as a parameter or in the coordinates.
	
	if isinstance(values[0], units.quantity.Quantity):
		l = [values[0], values[1]]
	else:
		if u == None:
			raise TypeError(f"Unit needs to be specified if the values don't have units; got {values} instead.")
		else:
			l = [values[0] * u, values[1] * u]

	return np.array(l, units.quantity.Quantity)

class Planet_group(pygame.sprite.Group):

	def __init__(self) -> None:
		super().__init__()
		self.offset:pygame.math.Vector2 = pygame.math.Vector2() #for the camera panning; no arguments means (0,0) coordinates
		self.scale = DEFAULTSCALE.copy()
		self.radiusToScale:bool = False
	
	auToPixels = lambda self, actualDimension: round((actualDimension * self.scale).value)
	#takes the actual position of celestial body and converts it to pixels

	def centralize(self) -> None:
		"""Resets the position of each planet in the group and zoom_scale""" #this is a docstring
		self.scale = DEFAULTSCALE.copy()
		self.offset *= 0

	def draw(self, surface, cursor_pos = (0, 0)): #-> None: #Overrides Group's draw method. This method violates Liskov substitution principle, and has a couple of other design problems that mypy points out. Also, the cursor_pos is currently unused because zooming based on cursor position still needs to be implemented.
		for planet in self.sprites():
			if self.radiusToScale:
				display_radius = self.auToPixels(planet.actualRadius)
			else:
				display_radius = planet.displayRadius

			planet_pos = pygame.Vector2(self.auToPixels(planet.position[0]), self.auToPixels(planet.position[1]) + HEIGHT/2) + self.offset #- center

			planet_rect = pygame.draw.circle(surface, planet.color, planet_pos, display_radius)
	
	def toggleRadius(self) -> None: #toggle the radii to scale or to display
		self.radiusToScale = not self.radiusToScale
	
	"""
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

class Body(pygame.sprite.Sprite):
	"""Class for any piece of matte"""
	
	def __init__(self, *groups, mass = None, position = None, velocity = None): #type: ignore
		super().__init__(*groups)

		#velocity should be a vector
		if velocity is None:
			self.velocity = create_array(m_per_s, (0, 0))
		
		elif isinstance(velocity, np.ndarray):
			self.velocity  = velocity

		else:
			raise TypeError(f"Velocity needs to be a numpy array with units, got {velocity} instead")
		
		if position is None:
			self.position = create_array(units.m, (0, 0))
		
		elif isinstance(position, np.ndarray):
			self.position  = position

		else:
			raise TypeError(f"Position needs to be a numpy array with units, got {position} instead.")

		if mass == None:
			self.mass = 0 * units.kg
		else:
			self.mass = mass

class CelestialBody(Body):

	def __init__(self, planet_group:Planet_group, displayRadius:int, color:RGB, mass:units.kg, actualRadius:units.m, distance_to_sun = None): #constructor: the init() function
		if distance_to_sun == None:
			distance_to_sun = 0 * units.m
		super().__init__(planet_group, mass = mass, position = create_array(values = (distance_to_sun, 0 * units.m))) #no need to pass in self for super()

		self.displayRadius = displayRadius
		self.actualRadius = actualRadius.to(units.m)
		self.color:RGB = color
		self.distance_to_sun =  distance_to_sun #initial/average distance to the sun

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


def pan_with_cursor(cursor_pos) -> pygame.Vector2: #enables camera panning with cursor near the edges of the screen
	cursor_x = cursor_pos[0]
	cursor_y = cursor_pos[1]
	left_border = SCREEN_BORDERS["left"]
	right_border = SCREEN_BORDERS["right"]
	top_border = SCREEN_BORDERS["top"]
	bottom_border = SCREEN_BORDERS["bottom"]
	BASE_VELOCITY = 1
	k = 1/50 #some constant to decrease the velocity
	offset:pygame.Vector2 = pygame.Vector2()

	if cursor_x <= left_border:
		offset.x = PANNING_VELOCITY * (left_border - cursor_x) * k + BASE_VELOCITY

	elif cursor_x >= WIDTH - right_border:
		offset.x = -PANNING_VELOCITY * (cursor_x - WIDTH + right_border) * k - BASE_VELOCITY

	if cursor_y <= top_border:
		offset.y = PANNING_VELOCITY * (top_border - cursor_y) * k + BASE_VELOCITY

	elif cursor_y >= HEIGHT - bottom_border:
		offset.y = -PANNING_VELOCITY * (cursor_y - HEIGHT + bottom_border) * k - BASE_VELOCITY
	
	return offset

def main():


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
		cursor_pos = pygame.mouse.get_pos()
		clock.tick(60)
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
					planet_group.scale *= event.y * ZOOM
				else:
					planet_group.scale /= -event.y * ZOOM
					
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
		planet_group.offset += pan_with_cursor(cursor_pos)
		
		screenPlanets.fill(BACKGROUND_COLOR)
		planet_group.draw(screenPlanets, (0,100))#cursor_pos)
		auPerPixel = round(((1*units.au).to(units.m)/planet_group.scale).value, 2) #How many aus a pixel represents
		scaleTxt = font.render("Scale: 1 pixel =  {:e}m".format(auPerPixel), True, (255,255,255))
		screenPlanets.blit(scaleTxt, (10, HEIGHT - 30)) #prints the scale on the pygame screen
		
		if planet_group.radiusToScale:
			radiiToScaleStr = "Radii and distances to scale."
		else:
			radiiToScaleStr = "Radii not to scale, but distances to scale."
		screenPlanets.blit(font.render(radiiToScaleStr, True, (255,255,255)), (10, HEIGHT - 60))
		pygame.display.flip()

	pygame.quit()

if __name__ == '__main__':
	main()