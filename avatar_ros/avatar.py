import pygame
from typing import List, Dict, Any
import sys
from random import randint, uniform, gauss
import math
from abc import ABC, abstractmethod
from copy import deepcopy

# Define FaceContext
FaceContext = Dict[str, Any]
INTERVAL = 33


class FaceModifier(ABC):
    @abstractmethod
    def apply(self, interval: int, face_context: FaceContext) -> FaceContext:
        pass


class BlinkModifier(FaceModifier):
    def __init__(self, open_min: int, open_max: int, close_min: int,
                 close_max: int):
        self.open_min = open_min
        self.open_max = open_max
        self.close_min = close_min
        self.close_max = close_max
        self.is_blinking = False
        self.next_toggle = randint(self.open_min, self.open_max)
        self.count = 0

    def linear_in_ease_out(self, fraction: float) -> float:
        if fraction < 0.25:
            return 1 - fraction * 4
        else:
            return (pow(fraction - 0.25, 2) * 16) / 9

    def apply(self, interval: int, face_context: FaceContext) -> FaceContext:
        eye_open = 1.0
        if self.is_blinking:
            fraction = self.linear_in_ease_out(self.count / self.next_toggle)
            eye_open = 0.2 + fraction * 0.8

        self.count += interval
        if self.count >= self.next_toggle:
            self.is_blinking = not self.is_blinking
            self.count = 0
            if self.is_blinking:
                self.next_toggle = randint(
                    self.close_min, self.close_max)
            else:
                self.next_toggle = randint(
                    self.open_min, self.open_max)

        for eye in face_context['eyes'].values():
            eye['open'] *= eye_open

        return face_context


class SaccadeModifier(FaceModifier):
    def __init__(self, update_min: int, update_max: int, gain: float):
        self.update_min = update_min
        self.update_max = update_max
        self.gain = gain
        self.next_toggle = uniform(self.update_min, self.update_max)
        self.saccade_x = 0
        self.saccade_y = 0

    def apply(self, tick_millis: int, face: FaceContext) -> FaceContext:
        self.next_toggle -= tick_millis
        if self.next_toggle < 0:
            self.saccade_x = gauss(0, self.gain)
            self.saccade_y = gauss(0, self.gain)
            self.next_toggle = uniform(self.update_min, self.update_max)

        for eye in face['eyes'].values():
            eye['gazeX'] += self.saccade_x
            eye['gazeY'] += self.saccade_y

        return face


class BreathModifier(FaceModifier):
    def __init__(self, duration: int):
        self.duration = duration
        self.time = 0

    def apply(self, tick_millis: int, face: FaceContext) -> FaceContext:
        self.time += tick_millis % self.duration
        face['breath'] = round(
            math.sin((2 * math.pi * self.time) / self.duration), 8)
        return face


class FaceRenderer:
    def __init__(self, screen: pygame.Surface, face_context: Dict[str, Any]) -> None:
        self.screen = screen
        self.original_width = screen.get_width()
        self.original_height = screen.get_height()
        self.current_context = face_context
        self.modifiers: List[FaceModifier] = []
        self.set_origin(320 // 2, 240 // 2)
        self.set_scale(1.0, 1.0)

    def set_origin(self, cx, cy):
        self.cx = cx
        self.cy = cy

    def set_scale(self, scale_x, scale_y):
        self.scale_x = scale_x
        self.scale_y = scale_y

    def add_modifier(self, modifier: FaceModifier) -> None:
        self.modifiers.append(modifier)

    def draw_eyes(self, cx: int, cy: int, radius: int,
                  eye_context: Dict[str, float]):
        scale = min(self.scale_x, self.scale_y)
        cx = int(self.cx + (cx - 160) * scale)
        cy = int(self.cy + (cy - 120) * scale)
        radius = int(radius * scale)
        gaze_x = eye_context.get('gazeX', 0) * 2
        gaze_y = eye_context.get('gazeY', 0) * 2
        open_ratio = eye_context.get('open', 1.0)

        # Draw eye white
        pygame.draw.ellipse(self.screen, 'white',
                          (cx - radius, cy - int(radius * open_ratio),
                           radius * 2, int(radius * 2 * open_ratio)))

        # Draw pupil
        if open_ratio > 0.2:  # Only draw pupil if eye is sufficiently open
            pupil_radius = int(radius * 0.4)
            pupil_x = int(cx + gaze_x)
            pupil_y = int(cy + gaze_y)
            pygame.draw.circle(self.screen, 'black',
                             (pupil_x, pupil_y), pupil_radius)

    def draw_mouth(self, cx: int, cy: int, minWidth: int, maxWidth: int,
                   minHeight: int, maxHeight: int,
                   mouth_context: Dict[str, float]) -> None:
        scale = min(self.scale_x, self.scale_y)
        cx = int(self.cx + (cx - 160) * scale)
        cy = int(self.cy + (cy - 120) * scale)
        minWidth = int(minWidth * scale)
        maxWidth = int(maxWidth * scale)
        minHeight = int(minHeight * scale)
        maxHeight = int(maxHeight * scale)
        openRatio = mouth_context['open']
        h = int(minHeight + (maxHeight - minHeight) * openRatio)
        w = int(minWidth + (maxWidth - minWidth) * (1 - openRatio))
        x = cx - w // 2
        y = cy - h // 2
        pygame.draw.rect(self.screen, 'white', (x, y, w, h))

    def move_face(self, dy: float) -> None:
        # In pygame, we'll redraw everything instead of moving individual objects
        pass

    def update(self, interval: int) -> None:
        context = deepcopy(self.current_context)
        for modifier in self.modifiers:
            context = modifier.apply(interval, context)
        self.render(context)

    def render(self, context: FaceContext) -> None:
        self.screen.fill('black')

        left_eye_coords = {'cx': 90, 'cy': 93, 'radius': 8}
        right_eye_coords = {'cx': 230, 'cy': 96, 'radius': 8}
        mouth_coords = {'cx': 160, 'cy': 148, 'minWidth': 50,
                        'maxWidth': 90, 'minHeight': 8, 'maxHeight': 58}

        # Apply breath effect to all coordinates
        dy = int(context['breath'] * 3 * min(self.scale_x, self.scale_y))
        left_eye_coords['cy'] += dy
        right_eye_coords['cy'] += dy
        mouth_coords['cy'] += dy

        self.draw_eyes(**left_eye_coords, eye_context=context['eyes']['left'])
        self.draw_eyes(**right_eye_coords,
                       eye_context=context['eyes']['right'])
        self.draw_mouth(**mouth_coords, mouth_context=context['mouth'])

        pygame.display.flip()


default_context = {
    'mouth': {'open': 0.0},
    'eyes': {
        'left': {'gazeX': 0.0, 'gazeY': 0.0, 'open': 1.0},
        'right': {'gazeX': 0.0, 'gazeY': 0.0, 'open': 1.0},
    },
    'breath': 0,
}


class AvatarFace():
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((320, 240), pygame.RESIZABLE)
        pygame.display.set_caption('Avatar')
        self.face_renderer = FaceRenderer(self.screen, default_context)
        self.running = False
        self.is_closed = False

        blink_modifier = BlinkModifier(
            open_min=400, open_max=5000, close_min=200, close_max=400)
        breath_modifier = BreathModifier(duration=6000)
        saccade_modifier = SaccadeModifier(
            update_min=300, update_max=2000, gain=0.2)

        self.face_renderer.add_modifier(blink_modifier)
        self.face_renderer.add_modifier(breath_modifier)
        self.face_renderer.add_modifier(saccade_modifier)

    def is_alive(self):
        return not self.is_closed

    def close(self):
        self.is_closed = True
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (event.w, event.h), pygame.RESIZABLE)
                self.face_renderer.set_origin(event.w // 2, event.h // 2)
                self.face_renderer.set_scale(event.w / 320, event.h / 240)

    def set_mouth_open(self, open):
        if open < 0 or math.isnan(open):
            open = 0
        if open > 1.0:
            open = 1.0
        self.face_renderer.current_context['mouth']['open'] = open

    def begin(self):
        self.running = True
        self.loop()

    def stop(self):
        self.running = False
        self.close()

    def loop(self, interval=INTERVAL):
        if not self.running:
            return
        self.handle_events()
        self.face_renderer.update(INTERVAL)


if __name__ == "__main__":
    avatar = AvatarFace()
    avatar.begin()
    clock = pygame.time.Clock()

    while avatar.is_alive():
        avatar.loop()
        clock.tick(1000 // INTERVAL)  # Maintain frame rate

    pygame.quit()
