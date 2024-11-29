import sys
from time import sleep
import pygame
from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import  Button
from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInversion:
    """overall class to mange game assets and behaviour."""
    def __init__(self):
        """initialize the game,and create game resources"""
        pygame.init()
        self.clock = pygame.time.Clock()
        self.settings = Settings()
        
        self.screen=pygame.display.set_mode((0,0),pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        #self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Alien Inversion")

        #create an instance to store game statistics,and create a scoreboard
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        #create an instance to store game statistics
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        #set the background colour.
        self.bg_colour = (230,230,230)

        #start alien invasion in an active state
        self.game_active = True

        #start alien inversion in an inactive state.
        self.game_active = False

        #make the play button.
        self.play_button = Button(self, "Play")

    def run_game(self):
        """start the main loop for the game."""
        while True:
            self._check_events()
            if self.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
            self._update_screen()
            self.clock.tick(60)

    def _check_events(self):
        #respond for keyboard and mouse events .
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self,mouse_pos):
        """start a new game when the player clicks play"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.game_active:
            #reset the game statistics
            self.stats.reset_stats()
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()
            self.settings.initialize_dynamic_settings()
            self.stats.reset_stats()
            self.game_active =True
            # hide the mouse curser
            pygame.mouse.set_visible(False)

        #get rid of any remaining bullect and aliens
        self.bullets.empty()
        self.aliens.empty()

        #create a new fleet and center the ship
        self._create_fleet()
        self.ship.center_ship()

    def _check_keydown_events(self,event):
        """respond to keypress"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        """respond to key release"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """create a new bullect and add it to the bullects group"""
        if len(self.bullets) < self.settings.bullet_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """update position of bullet and get rid of old bullets"""
        #update bullet positions
        self.bullets.update()

        #get rid of bullet that have disappeared
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                    self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """respond to build-alien collision"""
        #remove any bullet and aliens that have collied
        collisions =pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
                self.sb.prep_score()
                self.sb.check_high_score()

        if not self.aliens:
            #destroy existing bullet and create and create new fleet
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            #increase level
            self.stats.level +=1
            self.sb.prep_level()

    def _update_aliens(self):
        """check if the fleet is at an edge ,then update position"""
        self._check_fleet_edges()
        """update the position of all aliens in the fleet"""
        self.aliens.update()

        # look for alien -ship collisions
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        #look for aliens hitting the bottom of the screen
        self._check_aliens_bottom()

    def _create_fleet(self):
        """create the fleet of aliens"""
        #make an alien and keep adding aliens untill there's no room left
        #spaceing between aliens is one alien width
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        current_x, current_y = alien_width,alien_height
        while current_y < (self.settings.screen_height - 3 * alien_height):
            while current_x < (self.settings.screen_width -2 * alien_width  ):
                self._create_alien(current_x,current_y)
                current_x += 2 * alien_width

            #finished a row ; reset x value ,and increment y value
            current_x = alien_width
            current_y += 2 * alien_height

    def _check_fleet_edges(self):
        """respond approatately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """drop the entire fleet and change the flee's direction"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *=-1

    def _create_alien(self,x_position, y_position):
        """create an alien and place it in the fleet"""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien)

    def _ship_hit(self):
        """respond to the ship being hit by an alien"""
        if self.stats.ships_left > 0:
            #decrement ships_left and update score board
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            #get rid of any remaining bullet and aliens
            self.bullets.empty()
            self.aliens.empty()

            #create a new fleet and center the ship
            self._create_fleet()
            self.ship.center_ship()

            #pause
            sleep(0.5) 
        else:
            self.game_active =False
            pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
        """check if any aliens have reached the bottom of the screen"""
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.settings.screen_height:
                #treat thisw the same as if the ship got hit
                self._ship_hit()
                break


    def _update_screen(self):
         #update the screen during each pass through the loop.
            self.screen.fill(self.settings.bg_color)
            for bullet in self.bullets.sprites():
                bullet.draw_bullet()
            self.ship.blitme()
            self.aliens.draw(self.screen)

            #draw the score information
            self.sb.show_score()

            #draw the play button if the game is inactive
            if not self.game_active:
                self.play_button.draw_button()

            pygame.display.flip()


if __name__=='__main__':
    #make a game instance,and run the game.
    ai=AlienInversion()
    ai.run_game()

#the end