import logging
import random as rand
import simpy as sim
from collections import namedtuple


Client = namedtuple("Client", "cid arrival duration")


def window(env: sim.Environment,
           timed_agenda: list[tuple[float, float]],
           clients: sim.Store,
           win_num: int):
    for ts, te in timed_agenda:
        yield env.timeout(ts - env.now)
        logging.info(
            f"{env.now:.4f}: Window #{win_num} OPEN"
        )
    
        yield env.process(service(env, clients, te, win_num))


def service(env: sim.Environment,
            clients: sim.Store,
            when_close: float,
            win_num: int):
    while True:
        with clients.get() as client_req:
            close = env.timeout(when_close - env.now)
            event = yield client_req | close
        
            if client_req in event:
                client: Client = client_req.value
                logging.info(
                    f"{env.now:.4f}: Window #{win_num} BUSY "
                    f"by Client #{client.cid}"
                )

                yield env.timeout(client.duration)

                logging.info(f"{env.now:.4f}: Window #{win_num} FREE")
            else:
                logging.info(f"{env.now:.4f}: Window #{win_num} CLOSED")
                return


def clients_arriving(env: sim.Environment,
                     clients: sim.Store,
                     mean_arrival: float):
    cid = 1
    while True:
        yield env.timeout(rand.expovariate(1/mean_arrival))
        new_client = Client(cid, env.now, rand.uniform(1/60, 1/6))
        logging.info(f"{env.now:.4f}: Client #{new_client.cid} ARRIVES")

        yield clients.put(new_client)
        cid += 1


if __name__ == "__main__":
    rand.seed(42)

    logging.basicConfig(
        level=logging.INFO, filename="post.log", filemode="w"
    )

    env = sim.Environment(initial_time=8.5)
    
    clients = sim.Store(env)
    env.process(clients_arriving(env, clients, mean_arrival=1/2))

    windows_work_time = [
        [(8.5, 10.5), (11.5, 13.5)],
        [(8.5, 9.5), (10.5, 12.5)],
        [(11.5, 14.5)]
    ]
    for i, timed_agenda in enumerate(windows_work_time):
        env.process(window(env, timed_agenda, clients, i+1))

    env.run(until=13)
