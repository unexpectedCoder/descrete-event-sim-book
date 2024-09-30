import simpy as sim


class Car(object):
    def __init__(self, env: sim.Environment):
        self.env = env
        self.action = env.process(self.run())

    def run(self):
        while True:
            print(f'Start parking and charging at {self.env.now}')
            charge_duration = 5
            try:
                yield self.env.process(self.charge(charge_duration))
            except sim.Interrupt:
                print('Was interrupted. Hope, the battery is full enough ...')

            print(f'Start driving at {self.env.now}')
            trip_duration = 2
            yield self.env.timeout(trip_duration)

    def charge(self, duration):
        yield self.env.timeout(duration)


def driver(env, car):
    yield env.timeout(3)
    car.action.interrupt()


env = sim.Environment()
car = Car(env)
env.process(driver(env, car))
env.run(until=20)
