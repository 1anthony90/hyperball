import pygame, sys, socket, random, math
from PodSixNet.Connection import ConnectionListener, connection
from time import sleep, time
from pygame.locals import *

#uses parts of a client created for a simple movement simulator https://github.com/thebillington/pygame_multiplayer_server
class HyperBall(ConnectionListener):
    
    #checks to see if a point is inside a rectangle, for making the obstructions and points
    def isPointInsideRect(self, x, y, rect): #from pygame ch. 18
        if (x > rect.left) and (x < rect.right) and (y > rect.top) and (y < rect.bottom):
            return True
        else:
            return False
        
    #determines if two rectangles are overlapping 
    def doRecsOverlap(self, rec1, rec2): #from pygame ch. 18
        for a, b in [(rec1, rec2), (rec2, rec1)]:
            # Check if a's corners are inside b
            if ((self.isPointInsideRect(a.left, a.top, b)) or
                (self.isPointInsideRect(a.left, a.bottom, b)) or
                (self.isPointInsideRect(a.right, a.top, b)) or
                (self.isPointInsideRect(a.right, a.bottom, b))):
                return True
        return False
    
    #code for generating the 50 obstructions
    def createObstructions(self, amount):
        obstructions = []
        obstructionimg = pygame.image.load(self.location + "obstruction.png")
        while(len(obstructions)<amount):
            append = True
            tempobstruction = obstructionimg.get_rect()
            tempobstruction.topleft =(random.randint(0,self.WIDTH-tempobstruction.width),random.randint(0,self.HEIGHT-tempobstruction.height))
            for a in [self.playerone, self.playertwo]:
                if(tempobstruction.right >= (a.left-a.width) and tempobstruction.left <= (a.right+a.width)
                and tempobstruction.bottom >= (a.top-a.height) and tempobstruction.top <= (a.bottom+a.height)):
                    append = False
            if(append):
                obstructions.append(tempobstruction)
        return obstructions
    
    #general method to create non-overlapping sprites
    def createRecs(self, name, amount, allrectangles):
        sampleactorimg = pygame.image.load(self.location + name + ".png")
        newrecs = []
        while(len(newrecs)<amount):
            append = True
            temprec = sampleactorimg.get_rect()
            temprec.topleft = (random.randint(0,self.WIDTH-temprec.width),random.randint(0,self.HEIGHT-temprec.height))
            for rectangles in allrectangles:
                for a in rectangles:
                    if(self.doRecsOverlap(temprec,a)):
                        append = False
            if(append): 
                newrecs.append(temprec)
        return newrecs
    
    #packages rectangle information so that it can be sent across the network
    def package(self, reclist):
        infolist = []
        for rec in reclist:
            recinfo = {"left":rec.x,"top":rec.y,"width":rec.width,"height":rec.height}
            infolist.append(recinfo)
        return infolist
    def unpackage(self,infolist):
        i=0
        templist = []
        for info in infolist:
            templist.append(Rect(info["left"],info["top"],info["width"],info["height"]))
        return templist

    def prepare(self):
        prepareseconds = 3
        self.playerone.center = (self.WIDTH/3,self.HEIGHT/2)
        self.playertwo.center = (self.WIDTH * 2/3,self.HEIGHT/2)
        countdowntext = self.font80.render("Starting in {}".format(3-round(self.count/60,1)),1,(255,0,255))
        countdowntextwidth = self.WIDTH/2-countdowntext.get_width()/2
        firsttime = True
        while(self.count<prepareseconds*60):
            connection.Pump()
            self.Pump()
            self.checkExit()
            self.clock.tick(60)
            self.screen.fill(0)
            playernumbertext = self.font80.render("You are player {}".format(self.player+1), 1, (255,128,255))
            countdowntext = self.font80.render("Starting in {}".format(round(prepareseconds-self.count/60,1)),1,(255,128,255))
            self.draw()
            self.screen.blit(playernumbertext,(self.WIDTH/2-playernumbertext.get_width()/2,self.HEIGHT/2-playernumbertext.get_height()/2-40))
            self.screen.blit(countdowntext, (countdowntextwidth,self.HEIGHT/2-countdowntext.get_height()/2+40))
            pygame.display.flip()
            if firsttime:
                sleep(.5)
                firsttime=False
            self.count += 1
        self.count=0
        
    #automatically runs when the class is instantiated, sets up the entire game
    def __init__(self, host, port):
        pygame.init()
        pygame.font.init()
        self.WIDTH = 1366
        self.HEIGHT = 768
        self.speed = 7
        self.font40 = pygame.font.SysFont("Sans", 40)
        self.font80 = pygame.font.SysFont("Sans", 80)
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), FULLSCREEN)#paramater FULLSCREEN
        pygame.display.set_caption("Hyperball")
        self.clock = pygame.time.Clock()
        self.playeronescore = 0
        self.playertwoscore = 0
        self.count = 0
        self.connected = False
        self.exitnext = False
        self.alt = False
        self.gameended = False
        if getattr(sys, 'frozen', False):
            locationbackslash = sys._MEIPASS + "/"
            self.location = locationbackslash.replace("\\","/")
        else:
            self.location = ""
        self.backgroundimg = pygame.image.load(self.location + "background.png").convert()
        self.background = self.backgroundimg.get_rect()
        self.playeroneimg = pygame.image.load(self.location + "playerone.png")
        self.playerone = self.playeroneimg.get_rect()
        self.playerone.center = (self.WIDTH/3,self.HEIGHT/2)
        self.playertwoimg = pygame.image.load(self.location + "playertwo.png")
        self.playertwo = self.playertwoimg.get_rect()
        self.playertwo.center = (self.WIDTH * 2/3,self.HEIGHT/2)
        self.players = [self.playerone, self.playertwo]
        self.obstructionimg = pygame.image.load(self.location + "obstruction.png").convert()
        self.obstructions = self.createObstructions(50)
        self.pointimg = pygame.image.load(self.location + "point.png").convert()
        self.points = self.createRecs("point", 42, [self.players, self.obstructions])
        self.extrapointimg = pygame.image.load(self.location + "extrapoint.png").convert()
        self.extrapoints = self.createRecs("extrapoint", 6, [self.players, self.obstructions, self.points])
        self.TOTALSCORE = len(self.points) + len(self.extrapoints) * 3
        pygame.mouse.set_visible(False)
        scoretextone = self.font40.render("Player One Score: {}".format(self.playeronescore), 1, (250,0,0))
        self.scorelength = scoretextone.get_width()
        #multiplayer additions
        self.gameID = None
        self.player = None
        self.Connect((host,port))
        self.connected = True
        obstructionpackage = self.package(self.obstructions)
        pointpackage = self.package(self.points)
        extrapointpackage = self.package(self.extrapoints)    
        connection.Send({"action":"board","obstructions":obstructionpackage,"points":pointpackage,"extrapoints":extrapointpackage})
        self.running = False
        waitingtext = self.font40.render("Waiting for another player to connect...", 1, (0,255,255))
        self.screen.blit(waitingtext,(self.WIDTH/2-waitingtext.get_width()/2,self.HEIGHT/2-waitingtext.get_height()/2))
        pygame.display.flip()
        while (not self.running):
            self.checkExit()
            self.Pump()
            connection.Pump()
            sleep(.01)
        self.otherplayerconnected = True
        pygame.display.set_caption("Hyperball Game {} Player {}".format(self.gameID, self.player+1))
        self.prepare()
        
    #returns which sprite a player would hit if it moved
    def checkMovement(self, player, recs):    
        i = 0
        for a in recs:
            if(self.doRecsOverlap(player, a)):  
                return i
            i += 1
        return -1

    #moves the passed in player up
    def moveUp(self, player):
        if(player.top < self.speed):
            player.top = 0
        else:
            player.top -= self.speed
            while(self.checkMovement(player, self.obstructions) != -1):
                player.top += 1

    #moves the passed in player down
    def moveDown(self, player):
        if(player.bottom > self.HEIGHT-self.speed):
            player.bottom = self.HEIGHT
        else:
            player.top += self.speed
            while(self.checkMovement(player, self.obstructions) != -1):
                player.top -= 1

    #moves the passed in player left
    def moveLeft(self, player):
        if(player.left < self.speed):
            player.left = 0
        else:
            player.left -= self.speed
            while(self.checkMovement(player, self.obstructions) != -1):
                player.left += 1
                
    #moves the passed in player right
    def moveRight(self, player):
        if(player.right > self.WIDTH-self.speed):
            player.right = self.WIDTH
        else:
            player.left += self.speed
            while(self.checkMovement(player, self.obstructions) != -1):
                player.left -= 1

    #checks to see if players have scored and if the game is over, and awards points         
    def awardPoints(self):
        if(self.checkMovement(self.playerone, self.points) != -1):
            del self.points[self.checkMovement(self.playerone, self.points)]
            self.playeronescore += 1
            self.count = 0
        if(self.checkMovement(self.playerone, self.extrapoints) != -1):
            del self.extrapoints[self.checkMovement(self.playerone, self.extrapoints)]
            self.playeronescore += 3
            self.count = 0
        if(self.checkMovement(self.playertwo, self.points) != -1):
            del self.points[self.checkMovement(self.playertwo, self.points)]
            self.playertwoscore += 1
            self.count = 0
        if(self.checkMovement(self.playertwo, self.extrapoints) != -1):
            del self.extrapoints[self.checkMovement(self.playertwo, self.extrapoints)]
            self.playertwoscore += 3
            self.count = 0
        if(self.playeronescore > self.TOTALSCORE/2 or self.playertwoscore > self.TOTALSCORE/2 or self.count>600 or (self.playeronescore == 30 and self.playertwoscore == 30)):
            self.gameended = True

    #restarts the game        
    def restart(self):
        self.gameended = False
        self.playerone.center = (self.WIDTH/3,self.HEIGHT/2)
        self.playertwo.center = (self.WIDTH*2/3,self.HEIGHT/2)
        self.obstructions = self.createObstructions(50)
        self.points = self.createRecs("point", 42, [self.players, self.obstructions])
        self.extrapoints = self.createRecs("extrapoint", 6, [self.players, self.obstructions, self.points])
        self.count = 0
        self.playeronescore = 0
        self.playertwoscore = 0
        
    #draws all sprites and text
    def draw(self):
        self.screen.blit(self.backgroundimg, self.background)
        self.screen.blit(self.playeroneimg, self.playerone)
        self.screen.blit(self.playertwoimg, self.playertwo)
        for obstruction in self.obstructions:
            self.screen.blit(self.obstructionimg, obstruction)
        for point in self.points:
            self.screen.blit(self.pointimg, point)
        for extrapoint in self.extrapoints:
            self.screen.blit(self.extrapointimg, extrapoint)
        scoretextone = self.font40.render("Player One Score: {}".format(self.playeronescore), 1, (250,0,0))
        scoretexttwo = self.font40.render("Player Two Score: {}".format(self.playertwoscore), 1, (250,0,0))
        self.screen.blit(scoretextone, (self.WIDTH * 1/3 - self.scorelength/2,0))
        self.screen.blit(scoretexttwo, (self.WIDTH * 2/3 - self.scorelength/2,0))
        if(self.otherplayerconnected == False):
            disconnectedtext = self.font40.render("The other player has disconnected, press Alt+F4 to exit.", 1, (0,255,255))
            self.screen.blit(disconnectedtext,(self.WIDTH/2-disconnectedtext.get_width()/2,self.HEIGHT/3-disconnectedtext.get_height()/2))
        if(self.gameended == True):
            if(self.playeronescore>self.playertwoscore):
                finaltext = self.font80.render("Player One Wins!", 1, (255,255,255))
                self.screen.blit(finaltext,(self.WIDTH/2-finaltext.get_width()/2,self.HEIGHT/2-finaltext.get_height()/2))
            elif(self.playeronescore<self.playertwoscore):
                finaltext = self.font80.render("Player Two Wins!", 1, (255,255,255))
                self.screen.blit(finaltext,(self.WIDTH/2-finaltext.get_width()/2,self.HEIGHT/2-finaltext.get_height()/2))
            else:
                finaltext = self.font80.render("The Game is a Tie!", 1, (255,255,255))
                self.screen.blit(finaltext,(self.WIDTH/2-finaltext.get_width()/2,self.HEIGHT/2-finaltext.get_height()/2))

    #exits on alt-f4 and on close
    def checkExit(self):
        #Check if the user exited
        if self.exitnext:
            pygame.quit()
            sys.exit()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if(self.connected):
                    connection.Send({"action":"exit","player":self.player,"gameID":self.gameID})
                self.exitnext = True
            if event.type == KEYDOWN:
                if event.key == K_LALT:
                    self.alt = True
                if event.key == K_F4 and self.alt:
                    if(self.connected):
                        connection.Send({"action":"exit","player":self.player,"gameID":self.gameID})
                    self.exitnext = True
            if event.type == KEYUP:
                if event.key == K_LALT:
                    self.alt = False

    #checks which keys are pressed and calls movement and restart methods
    def checkKeys(self):
        self.speed = 7
        #Get the keys that are being pressed
        keys = pygame.key.get_pressed()
        if((keys[K_w] or keys[K_s]) and (keys[K_a] or keys[K_d])):
            self.speed = 5
        #Check which keys were pressed, update the position and notify the server of the update
        if keys[K_w]:
            self.moveUp(self.players[self.player])
        if keys[K_s]:
            self.moveDown(self.players[self.player])
        if keys[K_a]:
            self.moveLeft(self.players[self.player])
        if keys[K_d]:
            self.moveRight(self.players[self.player])
        if keys[K_r] and self.count>30:
            self.restart()
            obstructionpackage = self.package(self.obstructions)
            pointpackage = self.package(self.points)
            extrapointpackage = self.package(self.extrapoints)
            connection.Send({"action":"restart","player":self.player,"gameID":self.gameID,"obstructions":obstructionpackage,"points":pointpackage,"extrapoints":extrapointpackage})     
        if(keys[K_w] or keys[K_s] or keys[K_a] or keys[K_d]):
            connection.Send({"action":"update","x":self.players[self.player].x,"y":self.players[self.player].y,"player":self.player,"gameID":self.gameID})
        
    #update function runs the game, calls all of the neccesary methods
    def update(self):
        self.Pump()
        connection.Pump()
        self.checkExit()
        self.checkKeys()
        self.awardPoints()
        self.clock.tick(60)
        self.screen.fill(0)
        self.draw()
        pygame.display.flip()
        self.count += 1

    #Create a function to receive the start game signal
    def Network_initGame(self, data):
        #Get the game ID and player number from the data
        self.gameID = data["gameID"]
        self.player = data["player"]
        #Set the second player's board equal to the first
        if(self.player == 1):
            self.obstructions = self.unpackage(data["obstructions"])
            self.points = self.unpackage(data["points"])
            self.extrapoints = self.unpackage(data["extrapoints"])
            connection.Send({"action":"start","gameID":self.gameID})
        
    def Network_start(self, data):
        #Sets the games to start at the same time
        self.running = True
        
    #Create a function to update a player based on a message from the server
    def Network_move(self, data):
        
        #Get the non-client player
        if self.player == 0:
            p = 1
        elif self.player == 1:
            p = 0
        #Update the player data
        self.players[p].x = data["x"]
        self.players[p].y = data["y"]
        
    #Is called when the other player restarts        
    def Network_restart(self, data):
        self.restart()
        self.obstructions = self.unpackage(data["obstructions"])
        self.points = self.unpackage(data["points"])
        self.extrapoints = self.unpackage(data["extrapoints"])
        connection.Send({"action":"prepare","gameID":self.gameID})

    #Is sent to both clients at the same time so the games are synchronized on start
    def Network_prepare(self, data):
        self.count=0
        self.prepare()

    def Network_exit(self, data):
        self.otherplayerconnected = False
        
#game instantiation and loop
#hyper = HyperBall("localhost", 1337)
address = input("Address of the server: ")
if len(address) == 0:
    address = socket.gethostbyname(socket.gethostname())
hyper = HyperBall(address, 31425)
while True:
    hyper.update()
