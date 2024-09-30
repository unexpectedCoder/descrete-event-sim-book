import simpy as sim


def car(env: sim.Environment):
    while True:
        print('Start parking at %d' % env.now)
        parking_duration = 5
        yield env.timeout(parking_duration)

        print('Start driving at %d' % env.now)
        trip_duration = 2
        yield env.timeout(trip_duration)


env = sim.Environment()
env.process(car(env))
env.run(20)
