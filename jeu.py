import pygame
import random

# Initialisation de pygame
pygame.init()

# Dimensions de la fenêtre et de la carte
tile_size = 30
size = 20
width, height = size * tile_size, size * tile_size
interface_height = 100  # Hauteur supplémentaire pour l'interface

# Couleurs
PASSABLE_COLOR = (200, 200, 200)        # Gris clair pour les cases passables
PLAYER_COLOR = (0, 0, 255)              # Bleu pour le joueur
PLAYER_COLOR_LIGHT = (100, 100, 255)    # Bleu clair pour le joueur capable de bouger
ENEMY_COLOR = (255, 0, 0)               # Rouge pour les ennemis
ENEMY_COLOR_LIGHT = (255, 100, 100)     # Rouge clair pour les ennemis capables de bouger
SELECTED_COLOR = (0, 255, 0)            # Vert pour la sélection
OBJECTIVE_MAJOR_COLOR = (255, 255, 0)   # Jaune très clair pour objectif majeur (3 points)
OBJECTIVE_MINOR_COLOR = (255, 165, 0)   # Jaune foncé pour objectif mineur (1 point)

# Classe pour les unités
class Unit:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.selected = False
        self.moved = False  # Indicateur de mouvement pour le tour
        self.pv = 2  # Points de Vie
        self.attacked_this_turn = False  # Indicateur d'attaque dans ce tour
        self.visited_objectives = []  # Liste pour suivre les cases objectives visitées

    def draw(self, screen, units, objectives):
        """Affiche l'unité sur l'écran."""
        rect = pygame.Rect(self.x * tile_size, self.y * tile_size, tile_size, tile_size)
        if not self.moved:
            color = PLAYER_COLOR_LIGHT if self.color == PLAYER_COLOR else ENEMY_COLOR_LIGHT
        else:
            color = self.color
        pygame.draw.rect(screen, color, rect)

        if self.selected:
            pygame.draw.rect(screen, SELECTED_COLOR, rect, 3)

        font = pygame.font.SysFont(None, 16)
        symbols = self.get_symbols_on_same_tile(units)
        combined_text = font.render(symbols, True, (255, 255, 255))
        text_width = combined_text.get_width()
        text_x = self.x * tile_size + (tile_size - text_width) // 2
        screen.blit(combined_text, (text_x, self.y * tile_size + 5))

        for obj in objectives:
            if self.x == obj['x'] and self.y == obj['y']:
                pygame.draw.rect(screen, (0, 255, 0), rect, 1)

    def can_move(self, x, y, units):
        """Vérifie si l'unité peut se déplacer vers une case."""
        if 0 <= x < size and 0 <= y < size:
            if abs(self.x - x) <= 1 and abs(self.y - y) <= 1 and (x, y) != (self.x, self.y):
                # Vérifie si la case est libre
                if not any(u.x == x and u.y == y for u in units if u != self):
                    return True
        return False

    def move(self, x, y):
        """Déplace l'unité vers une case spécifiée."""
        self.x = x
        self.y = y
        self.moved = True

    def attack(self, target_unit, units, objectives):
        """Attaque une unité ennemie."""
        if self.can_move(target_unit.x, target_unit.y, units):
            dx = target_unit.x - self.x
            dy = target_unit.y - self.y
            new_x, new_y = target_unit.x + dx, target_unit.y + dy

            if target_unit.attacked_this_turn:
                target_unit.pv -= 1
                if target_unit.pv <= 0:
                    units.remove(target_unit)
                    return

            if not (0 <= new_x < size and 0 <= new_y < size) or any(u.x == new_x and u.y == new_y and u.color != target_unit.color for u in units):
                units.remove(target_unit)
            else:
                target_unit.move(new_x, new_y)
                target_unit.attacked_this_turn = True

    def get_symbols_on_same_tile(self, units):
        """Retourne les symboles des unités sur la même case."""
        symbols = [u.get_symbol() for u in units if u.x == self.x and u.y == self.y]
        return ' '.join(symbols)

    def get_symbol(self):
        """Retourne le symbole de l'unité."""
        return "U"

# Algorithme A* pour le pathfinding (limité à une case adjacente)
def a_star(start, goal, grid_size, units):
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Distance de Manhattan
    
    open_list = [(0, start)]  # (f_score, position)
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    
    while open_list:
        current = min(open_list, key=lambda x: x[0])[1]
        if current == goal or heuristic(current, start) == 1:  # Accepter une case adjacente
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return [start] + path[::-1]  # Inclure la position de départ + chemin inversé
        
        open_list = [x for x in open_list if x[1] != current]
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if (0 <= neighbor[0] < grid_size and 0 <= neighbor[1] < grid_size and
                not any(u.x == neighbor[0] and u.y == neighbor[1] for u in units if (u.x, u.y) != start)):  # Éviter les cases occupées sauf la position actuelle
                tentative_g_score = g_score[current] + 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, goal)
                    open_list.append((f_score[neighbor], neighbor))
    # Si aucun chemin vers la cible, retourner une case adjacente libre si possible
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        neighbor = (start[0] + dx, start[1] + dy)
        if (0 <= neighbor[0] < grid_size and 0 <= neighbor[1] < grid_size and
            not any(u.x == neighbor[0] and u.y == neighbor[1] for u in units)):
            return [neighbor]
    return []  # Pas de case adjacente libre

# Évaluation des actions possibles
def evaluate_action(unit, action, units, objectives):
    score = 1  # Score par défaut pour encourager le mouvement
    if action["type"] == "attack":
        target = action["target"]
        if target.pv <= 1:  # Peut tuer
            score += 50  # Très forte priorité pour tuer
        else:
            score += 40  # Forte priorité pour attaquer
        # Bonus si d'autres unités ennemies ciblent la même unité (coordination)
        nearby_allies = sum(1 for u in units if u.color == ENEMY_COLOR and u != unit and abs(u.x - target.x) <= 1 and abs(u.y - target.y) <= 1)
        score += nearby_allies * 5  # Bonus pour coordination
        # Pénalité si l'unité risque de mourir au tour suivant
        if any(u.color == PLAYER_COLOR and abs(u.x - unit.x) <= 1 and abs(u.y - unit.y) <= 1 for u in units):
            score -= 5
    elif action["type"] == "move":
        target_x, target_y = action["x"], action["y"]
        for obj in objectives:
            if obj["x"] == target_x and obj["y"] == target_y:
                score += 5 if obj["type"] == "MAJOR" else 2
        # Bonus pour se rapprocher d'un objectif ou d'une unité ennemie
        dist_to_closest_obj = min(abs(unit.x - obj["x"]) + abs(unit.y - obj["y"]) for obj in objectives)
        dist_to_closest_enemy = min(abs(unit.x - u.x) + abs(unit.y - u.y) for u in units if u.color == PLAYER_COLOR)
        new_dist_obj = min(abs(target_x - obj["x"]) + abs(target_y - obj["y"]) for obj in objectives)
        new_dist_enemy = min(abs(target_x - u.x) + abs(target_y - u.y) for u in units if u.color == PLAYER_COLOR)
        if new_dist_obj < dist_to_closest_obj:
            score += 2
        if new_dist_enemy < dist_to_closest_enemy:
            score += 1
        # Ajouter une petite composante aléatoire pour varier les choix
        score += random.uniform(0, 0.5)
    return score

# Tour de l'IA
def ai_turn(units, objectives, size, screen, game_map, tile_size):
    enemy_units = [u for u in units if u.color == ENEMY_COLOR and not u.moved]
    print(f"Nombre d'unités ennemies à jouer : {len(enemy_units)}")
    
    # Identifier les unités bleues déjà ciblées pour coordonner les attaques
    targeted_enemies = {}
    
    for unit in enemy_units:
        print(f"Unité à ({unit.x}, {unit.y})")
        # Lister les actions possibles (éviter les doublons)
        actions = []
        seen_positions = set()  # Pour éviter les doublons dans les mouvements
        
        # Attaquer
        attack_targets = [u for u in units if u.color == PLAYER_COLOR and unit.can_move(u.x, u.y, units)]
        if attack_targets:
            for target in attack_targets:
                actions.append({"type": "attack", "target": target})
                print(f"Action possible : Attaquer unité à ({target.x}, {target.y})")
                # Enregistrer que cette unité bleue est ciblée
                target_key = (target.x, target.y)
                targeted_enemies[target_key] = targeted_enemies.get(target_key, 0) + 1
        else:
            print("Aucune unité ennemie à portée d'attaque.")
        
        # Bouger vers un objectif
        for obj in objectives:
            path = a_star((unit.x, unit.y), (obj["x"], obj["y"]), size, units)
            if path and len(path) > 1:  # S'assurer qu'il y a une case suivante
                next_pos = path[1]  # Prendre la première case après la position actuelle
                if unit.can_move(next_pos[0], next_pos[1], units):
                    pos_key = (next_pos[0], next_pos[1])
                    if pos_key not in seen_positions:
                        actions.append({"type": "move", "x": next_pos[0], "y": next_pos[1]})
                        seen_positions.add(pos_key)
                        print(f"Action possible : Bouger vers objectif à ({next_pos[0]}, {next_pos[1]})")
        
        # Bouger vers une unité ennemie
        for target in [u for u in units if u.color == PLAYER_COLOR]:
            path = a_star((unit.x, unit.y), (target.x, target.y), size, units)
            if path and len(path) > 1:
                next_pos = path[1]
                if unit.can_move(next_pos[0], next_pos[1], units):
                    pos_key = (next_pos[0], next_pos[1])
                    if pos_key not in seen_positions:
                        actions.append({"type": "move", "x": next_pos[0], "y": next_pos[1]})
                        seen_positions.add(pos_key)
                        print(f"Action possible : Bouger vers ennemi à ({next_pos[0]}, {next_pos[1]})")
        
        # Si aucune action spécifique, tenter de bouger vers une case adjacente libre
        if not actions:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                next_x, next_y = unit.x + dx, unit.y + dy
                if unit.can_move(next_x, next_y, units):
                    pos_key = (next_x, next_y)
                    if pos_key not in seen_positions:
                        actions.append({"type": "move", "x": next_x, "y": next_y})
                        seen_positions.add(pos_key)
                        print(f"Action par défaut : Bouger vers ({next_x}, {next_y})")
                        break
        
        # Choisir la meilleure action
        if actions:
            best_action = max(actions, key=lambda a: evaluate_action(unit, a, units, objectives))
            print(f"Meilleure action : {best_action}")
            if best_action["type"] == "attack":
                unit.attack(best_action["target"], units, objectives)
                print(f"Attaque exécutée sur ({best_action['target'].x}, {best_action['target'].y})")
            elif best_action["type"] == "move":
                unit.move(best_action["x"], best_action["y"])
                print(f"Déplacement exécuté vers ({best_action['x']}, {best_action['y']})")
            
            # Mettre à jour l'affichage après chaque action
            screen.fill((0, 0, 0))
            draw_map(screen, game_map, tile_size)
            draw_objectives(screen, objectives, tile_size)
            for u in units:
                u.draw(screen, units, objectives)
            pygame.display.flip()
            
            # Gérer les événements pendant la pause pour éviter un gel
            start_time = pygame.time.get_ticks()
            while pygame.time.get_ticks() - start_time < 500:  # Pause de 500ms
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                pygame.time.wait(10)  # Petite pause pour éviter une surcharge CPU
        else:
            print("Aucune action possible pour cette unité.")

# Générer la carte
def generate_map(size):
    """Génère une carte de taille spécifiée."""
    return [[1 for _ in range(size)] for _ in range(size)]

# Afficher la carte
def draw_map(screen, game_map, tile_size):
    """Affiche la carte."""
    for y in range(size):
        for x in range(size):
            color = PASSABLE_COLOR
            pygame.draw.rect(screen, color, (x * tile_size, y * tile_size, tile_size, tile_size))

# Générer des unités sur des cases passables uniquement
def generate_units():
    """Génère les unités pour les joueurs et les ennemis."""
    units = []
    player_positions = [(0, i) for i in range(size)]
    enemy_positions = [(size - 1, i) for i in range(size)]

    player_positions = random.sample(player_positions, 5)
    enemy_positions = random.sample(enemy_positions, 5)

    player_units = [Unit(*pos, PLAYER_COLOR) for pos in player_positions]
    enemy_units = [Unit(*pos, ENEMY_COLOR) for pos in enemy_positions]
    
    units.extend(player_units)
    units.extend(enemy_units)
    
    return units

# Ajouter des objectifs à la carte
def add_objectives():
    """Ajoute des objectifs à la carte."""
    objectives = []
    center_x, center_y = size // 2, size // 2
    while True:
        x, y = random.randint(center_x - 3, center_x + 3), random.randint(center_y - 3, center_y + 3)
        if not any(obj['x'] == x and obj['y'] == y for obj in objectives):
            objectives.append({'x': x, 'y': y, 'type': 'MAJOR'})
            break

    for _ in range(3):
        while True:
            x, y = random.randint(center_x - 5, center_x + 5), random.randint(center_y - 5, center_y + 5)
            if not any(obj['x'] == x and obj['y'] == y for obj in objectives):
                objectives.append({'x': x, 'y': y, 'type': 'MINOR'})
                break

    return objectives

# Afficher les objectifs
def draw_objectives(screen, objectives, tile_size):
    """Affiche les objectifs sur la carte."""
    for obj in objectives:
        color = OBJECTIVE_MAJOR_COLOR if obj['type'] == 'MAJOR' else OBJECTIVE_MINOR_COLOR
        pygame.draw.rect(screen, color, (obj['x'] * tile_size, obj['y'] * tile_size, tile_size, tile_size))

# Calculer les scores
def calculate_scores(units, objectives, player_occupied_minor, player_occupied_major, enemy_occupied_minor, enemy_occupied_major):
    """Calcule les points à ajouter pour ce tour et met à jour les ensembles des cases occupées."""
    player_points_to_add = 0
    enemy_points_to_add = 0
    total_objectives = len(objectives)  # Nombre total de cases objectives (3 MINOR + 1 MAJOR = 4)

    # Compter les cases occupées par des unités
    for obj in objectives:
        obj_pos = (obj['x'], obj['y'])
        for unit in units:
            if unit.x == obj['x'] and unit.y == obj['y']:
                # Ajouter la case à l'historique de l'unité si elle n'y est pas déjà
                if obj_pos not in unit.visited_objectives:
                    unit.visited_objectives.append(obj_pos)

                # Vérifier si l'unité peut gagner des points sur cette case
                can_score = False
                # Premier détail : L'unité a-t-elle déjà visité cette case ?
                has_visited_before = unit.visited_objectives.count(obj_pos) > 1
                # Deuxième détail : Une autre unité du même camp a-t-elle déjà gagné des points sur cette case ?
                already_scored_by_team = False
                if unit.color == PLAYER_COLOR:
                    already_scored_by_team = (obj['type'] == 'MINOR' and obj_pos in player_occupied_minor) or \
                                             (obj['type'] == 'MAJOR' and obj_pos in player_occupied_major)
                else:
                    already_scored_by_team = (obj['type'] == 'MINOR' and obj_pos in enemy_occupied_minor) or \
                                             (obj['type'] == 'MAJOR' and obj_pos in enemy_occupied_major)

                # Vérifier si l'unité a visité toutes les autres cases objectives
                unique_visits = len(set(unit.visited_objectives))
                has_visited_all_others = unique_visits == total_objectives

                # Conditions pour marquer des points :
                # 1. C'est la première fois que l'unité visite cette case et que son camp marque des points dessus
                # 2. L'unité ou son camp a déjà marqué des points ici, mais elle a visité toutes les autres cases
                if not has_visited_before and not already_scored_by_team:
                    can_score = True
                elif (has_visited_before or already_scored_by_team) and has_visited_all_others:
                    can_score = True
                    # Réinitialiser l'historique de l'unité pour qu'elle puisse recommencer un tour
                    unit.visited_objectives = [obj_pos]
                    print(f"Unité à ({unit.x}, {unit.y}) a visité toutes les cases objectives, historique réinitialisé.")

                # Ajouter les points si les conditions sont remplies
                if can_score:
                    if unit.color == PLAYER_COLOR:
                        if obj['type'] == 'MINOR' and obj_pos not in player_occupied_minor:
                            player_occupied_minor.add(obj_pos)
                            player_points_to_add += 1
                            print(f"Joueur : Nouvelle case MINOR occupée à ({obj['x']}, {obj['y']}), +1 point")
                        elif obj['type'] == 'MAJOR' and obj_pos not in player_occupied_major:
                            player_occupied_major.add(obj_pos)
                            player_points_to_add += 3
                            print(f"Joueur : Nouvelle case MAJOR occupée à ({obj['x']}, {obj['y']}), +3 points")
                    elif unit.color == ENEMY_COLOR:
                        if obj['type'] == 'MINOR' and obj_pos not in enemy_occupied_minor:
                            enemy_occupied_minor.add(obj_pos)
                            enemy_points_to_add += 1
                            print(f"Ennemi : Nouvelle case MINOR occupée à ({obj['x']}, {obj['y']}), +1 point")
                        elif obj['type'] == 'MAJOR' and obj_pos not in enemy_occupied_major:
                            enemy_occupied_major.add(obj_pos)
                            enemy_points_to_add += 3
                            print(f"Ennemi : Nouvelle case MAJOR occupée à ({obj['x']}, {obj['y']}), +3 points")
                else:
                    print(f"Unité à ({unit.x}, {unit.y}) ne peut pas marquer de points sur ({obj['x']}, {obj['y']}) : "
                          f"has_visited_before={has_visited_before}, already_scored_by_team={already_scored_by_team}, "
                          f"unique_visits={unique_visits}/{total_objectives}")

    print(f"Points à ajouter ce tour - Joueur: {player_points_to_add}, Ennemi: {enemy_points_to_add}")
    return player_points_to_add, enemy_points_to_add

# Afficher le message de changement de tour
def draw_turn_indicator(screen, player_turn):
    """Affiche l'indicateur de tour."""
    font = pygame.font.SysFont(None, 36)
    text = "Joueur" if player_turn else "Ennemi"
    img = font.render(text, True, (255, 255, 255))
    screen.blit(img, (10, 10))

# Afficher le bouton de changement de tour
def draw_end_turn_button(screen, width, height, interface_height):
    """Affiche le bouton de fin de tour."""
    font = pygame.font.SysFont(None, 36)
    text = font.render("Terminé", True, (255, 255, 255))
    button_rect = pygame.Rect(width // 2 - 50, height, 100, interface_height - 10)
    pygame.draw.rect(screen, (100, 100, 100), button_rect)
    screen.blit(text, (width // 2 - 50 + 10, height + 10))

# Vérifier si le bouton de changement de tour est cliqué
def end_turn_button_clicked(mouse_pos, width, height, interface_height):
    """Vérifie si le bouton de fin de tour a été cliqué."""
    x, y = mouse_pos
    button_rect = pygame.Rect(width // 2 - 50, height, 100, interface_height - 10)
    return button_rect.collidepoint(x, y)

# Afficher les attributs de l'unité sélectionnée
def draw_unit_attributes(screen, unit, width, height, interface_height):
    """Affiche les attributs de l'unité sélectionnée."""
    if unit:
        font = pygame.font.SysFont(None, 24)
        pv_text = f"PV: {unit.pv} / 2"
        unit_img = font.render("Unité", True, (255, 255, 255))
        pv_img = font.render(pv_text, True, (255, 255, 255))
        screen.blit(unit_img, (10, height + 10))
        screen.blit(pv_img, (10, height + 40))

# Afficher les scores à gauche et à droite du bouton "Terminé"
def draw_scores(screen, player_score, enemy_score, width, height):
    """Affiche les scores des joueurs à côté du bouton Terminé."""
    font = pygame.font.SysFont(None, 24)
    player_score_text = f"Score Joueur: {player_score}"
    enemy_score_text = f"Score Ennemi: {enemy_score}"
    player_score_img = font.render(player_score_text, True, (255, 255, 255))
    enemy_score_img = font.render(enemy_score_text, True, (255, 255, 255))
    # Positionner à gauche et à droite du bouton "Terminé"
    screen.blit(player_score_img, (width // 2 - 200, height + 10))  # Décalé plus à gauche
    screen.blit(enemy_score_img, (width // 2 + 70, height + 10))   # À droite du bouton

# Afficher le message de victoire
def draw_victory_message(screen, message, width, height):
    """Affiche le message de victoire."""
    font = pygame.font.SysFont(None, 48)
    victory_img = font.render(message, True, (255, 255, 255))
    screen.blit(victory_img, (width // 2 - 100, height // 2 - 24))

# Configuration de la fenêtre
screen = pygame.display.set_mode((width, height + interface_height))
pygame.display.set_caption("Carte de 20x20 avec unités et déplacement")

# Générer une carte de 20 par 20
game_map = generate_map(size)

# Générer les unités
units = generate_units()

# Ajouter des objectifs
objectives = add_objectives()

# Initialisation des variables
selected_unit = None
player_turn = True  # True pour le tour du joueur, False pour le tour de l'ennemi
player_score = 0  # Score initial à 0
enemy_score = 0  # Score initial à 0
victory = False
victory_message = ""

# Ensembles pour suivre les cases occupées (pour éviter de recompter les mêmes cases)
player_occupied_minor = set()
player_occupied_major = set()
enemy_occupied_minor = set()
enemy_occupied_major = set()

# Boucle principale du jeu
running = True
while running:
    if not victory:
        if player_turn:  # Tour du joueur
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if end_turn_button_clicked((x, y), width, height, interface_height):
                        print("Tour du joueur terminé, passage au tour de l'IA.")
                        player_turn = False  # Passer au tour de l'IA
                        # Déclencher le tour de l'IA
                        ai_turn(units, objectives, size, screen, game_map, tile_size)
                        # Après le tour de l'IA, revenir automatiquement au tour du joueur
                        print("Tour de l'IA terminé, retour au tour du joueur.")
                        for unit in units:
                            unit.moved = False
                            unit.attacked_this_turn = False
                        player_turn = True  # Revenir au tour du joueur
                        # Mettre à jour les scores
                        player_points_to_add, enemy_points_to_add = calculate_scores(
                            units, objectives, player_occupied_minor, player_occupied_major,
                            enemy_occupied_minor, enemy_occupied_major
                        )
                        player_score += player_points_to_add
                        enemy_score += enemy_points_to_add

                        if player_score >= 50:
                            victory = True
                            victory_message = "Victoire Joueur!"
                        elif enemy_score >= 50:
                            victory = True
                            victory_message = "Victoire Ennemi!"
                        elif not any(unit.color == PLAYER_COLOR for unit in units):
                            victory = True
                            victory_message = "Victoire Ennemi!"
                        elif not any(unit.color == ENEMY_COLOR for unit in units):
                            victory = True
                            victory_message = "Victoire Joueur!"
                    else:
                        grid_x, grid_y = x // tile_size, y // tile_size
                        if event.button == 1:  # Clic gauche pour sélectionner
                            possible_units = [u for u in units if u.x == grid_x and u.y == grid_y and not u.moved and u.color == PLAYER_COLOR]
                            if selected_unit in possible_units:
                                current_index = possible_units.index(selected_unit)
                                selected_unit.selected = False
                                selected_unit = possible_units[(current_index + 1) % len(possible_units)]
                            else:
                                if selected_unit:
                                    selected_unit.selected = False
                                if possible_units:
                                    selected_unit = possible_units[0]
                            if selected_unit:
                                selected_unit.selected = True
                        elif event.button == 3:  # Clic droit pour déplacer ou attaquer
                            if selected_unit and selected_unit.color == PLAYER_COLOR:
                                target_unit = [u for u in units if u.x == grid_x and u.y == grid_y and u.color != selected_unit.color]
                                for cible in target_unit:
                                    selected_unit.attack(cible, units, objectives)
                                    # Recalculer les scores après une attaque
                                    player_points_to_add, enemy_points_to_add = calculate_scores(
                                        units, objectives, player_occupied_minor, player_occupied_major,
                                        enemy_occupied_minor, enemy_occupied_major
                                    )
                                    player_score += player_points_to_add
                                    enemy_score += enemy_points_to_add
                                if selected_unit.can_move(grid_x, grid_y, units):
                                    selected_unit.move(grid_x, grid_y)
                                    selected_unit.selected = False
                                    selected_unit = None
                                    # Recalculer les scores après chaque déplacement
                                    player_points_to_add, enemy_points_to_add = calculate_scores(
                                        units, objectives, player_occupied_minor, player_occupied_major,
                                        enemy_occupied_minor, enemy_occupied_major
                                    )
                                    player_score += player_points_to_add
                                    enemy_score += enemy_points_to_add

        # Mise à jour de l'affichage
        screen.fill((0, 0, 0))
        draw_map(screen, game_map, tile_size)
        draw_objectives(screen, objectives, tile_size)
        
        for unit in units:
            unit.draw(screen, units, objectives)

        draw_turn_indicator(screen, player_turn)
        draw_end_turn_button(screen, width, height, interface_height)
        draw_unit_attributes(screen, selected_unit, width, height, interface_height)
        draw_scores(screen, player_score, enemy_score, width, height)  # Afficher les scores à côté du bouton

        if victory:
            draw_victory_message(screen, victory_message, width, height)
            pygame.display.flip()
            pygame.time.wait(5000)
            running = False

        pygame.display.flip()

pygame.quit()