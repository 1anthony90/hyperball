import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame, sys, socket, random, pyperclip, hyperballsingle
from PodSixNet.Connection import ConnectionListener, connection
from time import sleep
from pygame.locals import *

#uses parts of a client created for a simple movement simulator: https://github.com/thebillington/pygame_multiplayer_server
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
        while(len(obstructions)<amount):
            append = True
            tempobstruction = self.obstructionimg.get_rect()
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
        self.count = 0
        countdowntext = self.font80.render("Starting in {}".format(3-round(self.count/self.TICKRATE,1)),1,(255,0,255))
        countdowntextwidth = self.WIDTH/2-countdowntext.get_width()/2
        firsttime = True
        self.movementlock = True
        while(self.count<prepareseconds*self.TICKRATE):
            connection.Pump()
            self.Pump()
            self.checkExit()
            self.clock.tick(self.TICKRATE)
            self.screen.fill(0)
            playernumbertext = self.font80.render("You are player {}".format(self.player+1), 1, (255,128,255))
            countdowntext = self.font80.render("Starting in {}".format(round(prepareseconds-self.count/self.TICKRATE,1)),1,(255,128,255))
            self.draw()
            self.screen.blit(playernumbertext,(self.WIDTH/2-playernumbertext.get_width()/2,self.HEIGHT/2-playernumbertext.get_height()/2-40))
            self.screen.blit(countdowntext, (countdowntextwidth,self.HEIGHT/2-countdowntext.get_height()/2+40))
            pygame.display.flip()
            if firsttime:
                sleep(.5)
                firsttime=False
            self.count += 1
        self.movementlock = False
        self.count=0
        
    #automatically runs when the class is instantiated, sets up the entire game
    def __init__(self):
        pygame.init()
        pygame.font.init()
        #optimizes program by only checking certain events
        pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP])
        pygame.key.set_repeat(500,50)
        self.TICKRATE = 60
        self.WIDTH = 1366
        self.HEIGHT = 768
        self.speed = 7
        self.font30 = pygame.font.SysFont("Sans", 30)
        self.font40 = pygame.font.SysFont("Sans", 40)
        self.font80 = pygame.font.SysFont("Sans", 80)
        #these settings get used in the creation of the screen and improve performance
        settings = FULLSCREEN | NOFRAME #| DOUBLEBUF | HWSURFACE
        self.screen = pygame.display.set_mode((self.WIDTH,self.HEIGHT), settings)
        pygame.display.set_caption("Hyperball")
        self.clock = pygame.time.Clock()
        self.gamestate = "mainmenu"
        self.address = ""
        self.selected = 0
        self.playeronescore = 0
        self.playertwoscore = 0
        self.count = 0
        self.inhibitor = -16
        self.connected = False
        self.exitnext = False
        self.escapenext = False
        self.alt = False
        self.ctrl = False
        self.gameended = False
        self.movementlock = False
        if hasattr(sys, '_MEIPASS'):
            locationbackslash = sys._MEIPASS + "/"
            self.location = locationbackslash.replace("\\","/")
        else:
            self.location = ""
        self.menuimg = pygame.image.load(self.location + "menu.png")
        self.menu1 = self.menuimg.get_rect()
        self.menu1.center = (self.WIDTH/2, self.HEIGHT/2-self.menu1.height)
        self.menu2 = self.menuimg.get_rect()
        self.menu2.center = (self.WIDTH/2, self.HEIGHT/2+self.menu2.height)
        self.menu3 = self.menuimg.get_rect()
        self.menu3.center = (self.WIDTH/2, self.HEIGHT/2)
        self.selectorimg = pygame.image.load(self.location + "selector.png")
        self.selector = self.selectorimg.get_rect()
        self.selector.center = (self.WIDTH/2, self.HEIGHT/2+self.menu1.height/2)
        self.backgroundimg = pygame.image.load(self.location + "background.png").convert()
        self.background = self.backgroundimg.get_rect()
        self.playeroneimg = pygame.image.load(self.location + "playerone.png").convert_alpha()
        self.playerone = self.playeroneimg.get_rect()
        self.playerone.center = (self.WIDTH/3,self.HEIGHT/2)
        self.playertwoimg = pygame.image.load(self.location + "playertwo.png").convert_alpha()
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

    def initMultiplayer(self, host, port):
        #multiplayer additions
        self.gameID = None
        self.player = None
        self.opponentsent = False
        self.moveingup = False
        self.moveingdown = False
        self.moveingleft = False
        self.moveingright = False
        self.Connect((host,port))
        self.connected = True
        obstructionpackage = self.package(self.obstructions)
        pointpackage = self.package(self.points)
        extrapointpackage = self.package(self.extrapoints)    
        connection.Send({"action":"board","obstructions":obstructionpackage,"points":pointpackage,"extrapoints":extrapointpackage})
        self.running = False
        waitingtext = self.font40.render("Waiting for another player to connect...", 1, (0,255,255))
        self.screen.blit(waitingtext,(self.WIDTH/2-waitingtext.get_width()/2,self.HEIGHT/4-waitingtext.get_height()/2))
        pygame.display.flip()
        while (not self.running):
            self.checkExit()
            self.Pump()
            connection.Pump()
            sleep(.01)
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
        if(self.playeronescore > self.TOTALSCORE/2 or self.playertwoscore > self.TOTALSCORE/2 or self.count>(10*self.TICKRATE) or (self.playeronescore == 30 and self.playertwoscore == 30)):
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
        fps = self.font40.render(str(int(self.clock.get_fps())), 1, (255,255,255))
        self.screen.blit(fps,(0,0))
        scoretextone = self.font40.render("Player One Score: {}".format(self.playeronescore), 1, (250,0,0))
        scoretexttwo = self.font40.render("Player Two Score: {}".format(self.playertwoscore), 1, (250,0,0))
        self.screen.blit(scoretextone, (self.WIDTH * 1/3 - self.scorelength/2,0))
        self.screen.blit(scoretexttwo, (self.WIDTH * 2/3 - self.scorelength/2,0))
        if(self.running == False):
            disconnectedtext = self.font40.render("The other player has disconnected, press Escape to leave.", 1, (0,255,255))
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

    def menuDraw(self):
        self.screen.blit(self.backgroundimg, self.background)
        self.screen.blit(self.menuimg, self.menu1)        
        self.screen.blit(self.menuimg,self.menu2)
        menu1text = self.font80.render("Internet",1,(255,255,255))
        menu2text = self.font80.render("Local",1,(255,255,255))
        self.screen.blit(menu1text,(self.WIDTH/2-menu1text.get_width()/2,self.menu1.centery-menu1text.get_height()/2))
        self.screen.blit(menu2text,(self.WIDTH/2-menu2text.get_width()/2,self.menu2.centery-menu2text.get_height()/2))
        if self.selected % 2 == 0:
            self.screen.blit(self.selectorimg,(self.WIDTH/2-self.selector.width/2,self.menu1.y-10))
        elif self.selected % 2 == 1:
            self.screen.blit(self.selectorimg,(self.WIDTH/2-self.selector.width/2,self.menu2.y-10))

    def multiplayerMenuDraw(self):
        self.screen.blit(self.backgroundimg, self.background)
        self.screen.blit(self.menuimg, self.menu3)
        addressprompt = self.font30.render("IP Address:",1,(255,255,255))
        addresstext = self.font40.render(self.address,1,(255,0,0))
        self.screen.blit(addressprompt,(self.menu3.left+10,self.menu3.top+10))
        self.screen.blit(addresstext,(self.WIDTH/2-addresstext.get_width()/2,self.menu3.centery-addresstext.get_height()/2))
        
    #exits on alt-f4 and on close
    def checkExit(self):
        #Check if the user exited
        if self.exitnext:
            pygame.quit()
            sys.exit()
        if self.escapenext:
            self.gamestate = "mainmenu"
        for event in pygame.event.get():
            if event.type == QUIT:
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
                if event.key == K_ESCAPE:
                    if(self.connected):
                        connection.Send({"action":"exit","player":self.player,"gameID":self.gameID})
                    self.escapenext = True
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
            self.movementlock = True
            self.restart()
            obstructionpackage = self.package(self.obstructions)
            pointpackage = self.package(self.points)
            extrapointpackage = self.package(self.extrapoints)
            connection.Send({"action":"restart","player":self.player,"gameID":self.gameID,"obstructions":obstructionpackage,"points":pointpackage,"extrapoints":extrapointpackage})     
        #if(keys[K_w] or keys[K_s] or keys[K_a] or keys[K_d]):
        #must send every loop so the other client can tell whether information was missed
        connection.Send({"action":"update","x":self.players[self.player].x,"y":self.players[self.player].y,"player":self.player,"gameID":self.gameID})
        if self.player == 0:
            p = 1
        elif self.player == 1:
            p = 0
        #if the client did not recieve any sent data from the other client, then extrapolate
        if (self.opponentsent == False):
            if self.moveingup:
                self.moveUp(self.players[p])
            elif self.moveingdown:
                self.moveDown(self.players[p])
            if self.moveingleft:
                self.moveLeft(self.players[p])
            elif self.moveingright:
                self.moveRight(self.players[p])
        #has to set opponentsent to False so that on the next loop this client must recieve an update or else it will move the player through extrapolation
        else:
            self.opponentsent = False
            
    def menuCheckKeys(self):
        keys = pygame.key.get_pressed()
        if (keys[K_UP] or keys[K_w]) and (self.inhibitor<self.count-15):
            self.selected += 1
            self.inhibitor = self.count
        if (keys[K_DOWN] or keys[K_s]) and (self.inhibitor<self.count-15):
            self.selected -= 1
            self.inhibitor = self.count
        if keys[K_RETURN]:
            if self.selected % 2 == 0:
                self.gamestate = "multiplayermenu"
                #self.initMultiplayer(address, 31425)
            elif self.selected % 2 == 1:
                self.selected = 0
                self.spgame = hyperballsingle.HyperBall()
                self.gamestate = "singleplayer"
                
    def getInput(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_LALT:
                    self.alt = True
                elif event.key == K_LCTRL or event.key == K_RCTRL:
                    self.ctrl = True
                elif event.key == K_F4 and self.alt:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_v and self.ctrl:
                    self.address += pyperclip.paste()
                    self.address = self.address[:15]
                elif event.key == K_ESCAPE:
                    self.gamestate = "mainmenu"
                elif event.key == K_RETURN:
                    self.initMultiplayer(self.address, 31425)
                    self.gamestate = "multiplayer"
                elif event.key == K_BACKSPACE:
                    self.address = self.address[:-1]
                    self.count = 0
                else:
                    self.address += event.unicode
                    self.address = self.address[:15]
            elif event.type == KEYUP:
                if event.key == K_LALT:
                    self.alt = False
                if event.key == K_LCTRL or event.key == K_RCTRL:
                    self.ctrl = False

                    
    #update function runs the game, calls all of the neccesary methods
    def update(self):
        if self.gamestate == "mainmenu":
            self.checkExit()
            self.menuCheckKeys()
            self.clock.tick(self.TICKRATE)
            self.screen.fill(0)
            self.menuDraw()
            pygame.display.flip()
            self.count += 1
        elif self.gamestate == "multiplayermenu":
            self.getInput()
            self.clock.tick(self.TICKRATE)
            self.screen.fill(0)
            self.multiplayerMenuDraw()
            pygame.display.flip()
        elif self.gamestate == "multiplayer":
            self.Pump()
            connection.Pump()
            self.checkExit()
            if(self.movementlock == False):
                self.checkKeys()
            self.awardPoints()
            self.clock.tick(self.TICKRATE)
            self.screen.fill(0)
            self.draw()
            pygame.display.flip()
            self.count += 1
        elif self.gamestate == "singleplayer":
            self.spgame.update()
            if pygame.key.get_pressed()[K_ESCAPE]:
                self.gamestate = "mainmenu"

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
        #elif self.player == 1:
        else:
            p = 0
        #Update the player data and what direction the player last moved in
        if(self.movementlock == False):
            self.opponentsent = True
            oldx = self.players[p].x
            oldy = self.players[p].y
            self.players[p].x = data["x"]
            self.players[p].y = data["y"]
            if(oldx > self.players[p].x):
                self.moveingleft = True
            elif(oldx < self.players[p].x):
                self.moveingright = True
                self.moveingleft = False
            else:
                self.moveingleft = None
                self.moveingright = None
            if(oldy > self.players[p].y):
                self.moveingup = True
            elif(oldy < self.players[p].y):
                self.moveingdown = True
                self.moveingup = False
            else:
                self.moveingup = False
                self.moveingdown = False
                self.moveingleft = False
                self.moveingright = False         

    #Is called when the other player restarts        
    def Network_restart(self, data):
        self.restart()
        self.obstructions = self.unpackage(data["obstructions"])
        self.points = self.unpackage(data["points"])
        self.extrapoints = self.unpackage(data["extrapoints"])
        connection.Send({"action":"prepare","gameID":self.gameID})

    #Is sent to both clients at the same time so the games are synchronized on start
    def Network_prepare(self, data):
        self.prepare()

    def Network_exit(self, data):
        self.running = False
        
#game instantiation and loop
#hyper = HyperBall("localhost", 1337)
#address = input("Address of the server: ")
#if len(address) == 0:
#    address = socket.gethostbyname(socket.gethostname())
hyper = HyperBall()
while True:
    hyper.update()
