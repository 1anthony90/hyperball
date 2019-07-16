#is an adapted server from a simple movement simulator https://github.com/thebillington/pygame_multiplayer_server
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import socket
from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from time import sleep

class ClientChannel(Channel):
    #Create a function that will update the other player on movement
    def Network_update(self, data):
        
        #Fetch the data top help us identify which game needs to update
        gameID = data["gameID"]
        player = data["player"]
        x = data["x"]
        y = data["y"]
        
        #Call the move function of the server to update this game
        self._server.sendMovement(x, y, gameID, player)

    #sends restart command to the other client
    def Network_restart(self, data):
        self._server.sendRestart(data["gameID"], data["player"], data["obstructions"], data["points"], data["extrapoints"])

    #stores the board data
    def Network_board(self, data):
        self._server.sendBoard(data["obstructions"], data["points"], data["extrapoints"])

    def Network_start(self, data):
        self._server.sendStart(data["gameID"])

    def Network_prepare(self, data):
        self._server.sendPrepare(data["gameID"])

    def Network_exit(self, data):
        self._server.sendExit(data["player"], data["gameID"])
    
class GameServer(Server):

    #Set the channel to deal with incoming requests
    channelClass = ClientChannel

    #Constructor to initialize the server objects
    def __init__(self, *args, **kwargs):
        #Call the super constructor
        Server.__init__(self, *args, **kwargs)
        #Create the objects to hold our game ID and list of running games
        self.games = []
        self.queue = None
        self.gameIndex = 0

    #Function to deal with new connections
    def Connected(self, channel, addr):
        print("New connection: {}".format(channel))

        #When we receive a new connection
        #Check whether there is a game waiting in the queue
        if self.queue == None:

            #If there isn't someone queueing
            #Set the game ID for the player channel
            #Add a new game to the queue
            channel.gameID = self.gameIndex
            self.queue = Game(channel, self.gameIndex)

        else:

            #Set the game index for the currently connected channel
            channel.gameID = self.gameIndex

            #Set the second player channel
            self.queue.player_channels.append(channel)

            #Send a message to the clients that the game is starting
            for i in range(0, len(self.queue.player_channels)):
                self.queue.player_channels[i].Send({"action":"initGame","player":i,"gameID":self.queue.gameID,"obstructions":self.obstructions,"points":self.points,"extrapoints":self.extrapoints})

            #Add the game to the end of the game list
            self.games.append(self.queue)

            #Empty the queue ready for the next connection
            self.queue = None
            
            #Increment the game index for the next game
            self.gameIndex += 1
            
    #Create a function to move the players of a game
    def sendMovement(self, x, y, gameID, player):
        #Get the game
        g = self.games[gameID]
		
	#For all the other players send a message to update their position
        for i in range(0, len(g.player_channels)):		
	    #If we aren't looking at the player that moved
            if i != player:		
		#Send a message to update
                g.player_channels[i].Send({"action":"move","x":x,"y":y})

    def sendRestart(self, gameID, player, obstructions, points, extrapoints):
        g = self.games[gameID]
        for i in range(0, len(g.player_channels)):
            if i != player:
                g.player_channels[i].Send({"action":"restart","obstructions":obstructions,"points":points,"extrapoints":extrapoints})

    def sendBoard(self, obstructions, points, extrapoints):
        self.obstructions = obstructions
        self.points = points
        self.extrapoints = extrapoints

    def sendStart(self, gameID):
        g = self.games[gameID]
        for i in range(0, len(g.player_channels)):
            g.player_channels[i].Send({"action":"start"})

    def sendPrepare(self, gameID):
        g = self.games[gameID]
        for i in range(0, len(g.player_channels)):
            g.player_channels[i].Send({"action":"prepare"})
    def sendExit(self, player, gameID):
        #Get the game
        g = self.games[gameID]
		
	#For all the other players send a message to update their position
        for i in range(0, len(g.player_channels)):		
	    #If we aren't looking at the player that moved
            if i != player:		
		#Send an exited method
                g.player_channels[i].Send({"action":"exit"})
        
#Create the game class to hold information about any particular game
class Game(object):

    #Constructor
    def __init__(self, playerchannel, gameIndex):

        #Store the network channel of the first client
        self.player_channels = [playerchannel]

        #Set the game id
        self.gameID = gameIndex
        
#gets the local ip address and starts the server
ipaddress = socket.gethostbyname(socket.gethostname())
port = 31425
print("Server starting on {}".format(ipaddress))
pygame.init()
#Create a server
#server = GameServer(localaddr=("localhost", 1337))
server = GameServer(localaddr=(ipaddress, port))
#Pump the server at regular intervals (check for new requests)
while True:
    server.Pump()
