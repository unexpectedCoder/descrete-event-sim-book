import logging
import random as rand
import simpy as sim


class Client:
    av_wait_time = 15/60
    av_service_time = 10/60

    def __init__(self, env: sim.Environment, cid: int):
        self.env = env
        self.cid = cid

        self.arrive_time = env.now
        self.satisfied = False
        self.waiting_time = 0
        self.total_time = 0
    
    def get_service(self, workers: sim.Store):
        with workers.get() as worker_req:
            dt_patience = rand.expovariate(1 / self.av_wait_time)
            patience = self.env.timeout(dt_patience)
            worker_or_patience = yield worker_req | patience

            self.waiting_time = self.env.now - self.arrive_time

            if worker_req in worker_or_patience:
                worker = worker_req.value
                logging.info(
                    f"{self.env.now:.4f}: "
                    f"Worker #{worker.wid} STARTS service "
                    f"the Client #{self.cid}"
                )
            
                yield self.env.process(worker.service(self))
                
                logging.info(
                    f"{self.env.now:.4f}: "
                    f"Worker #{worker.wid} ENDS service "
                    f"the Client #{self.cid}"
                )

                self.satisfied = True
                self.total_time = self.env.now - self.arrive_time
            else:
                logging.info(
                    f"{self.env.now:.4f}: Client #{self.cid} is GONE"
                )


class Worker:
    def __init__(self,
                 env: sim.Environment,
                 wid: int,
                 timed_agenda: list[tuple[float, float]]):
        self.env = env
        self.wid = wid
        self.timed_agenda = timed_agenda

        self.when_end: float = None
        self.clients = []
        self.start_event = env.event()
        self.get_free_event = env.event()
    
    def work(self):
        for ts, te in self.timed_agenda:
            self.when_end = te
            yield self.env.timeout(ts - self.env.now)
            logging.info(
                f"{self.env.now:.4f}: Worker #{self.wid} WORKS"
            )

            self.start_event.succeed(self)
            self.start_event = self.env.event()

    def service(self, client: Client):
        dt = rand.expovariate(1/client.av_service_time)
        yield self.env.timeout(dt)
        self.clients.append(client)

        if env.now < self.when_end:
            self.get_free_event.succeed(self)
            self.get_free_event = self.env.event()
        else:
            logging.info(
                f"{self.env.now:.4f}: Worker #{self.wid} RELAXES"
            )


class Bank:
    av_incoming_time = 6/60

    def __init__(self, env: sim.Environment, workers: list[Worker]):
        self.env = env
        
        self.workers_list = workers.copy()
        self.workers = sim.Store(env, len(workers))
        self.clients: list[Client] = []

    def operate(self):
        for w in self.workers_list:
            self.env.process(w.work())
        self.env.process(self.add_workers())
        self.env.process(self.free_workers())
        self.env.process(self.clients_incoming())
    
    def add_workers(self):
        while True:
            starts = [w.start_event for w in self.workers_list]
            any_of = yield self.env.any_of(starts)
            for worker in any_of.values():
                yield self.workers.put(worker)
    
    def free_workers(self):
        while True:
            ends = [w.get_free_event for w in self.workers_list]
            any_of = yield self.env.any_of(ends)
            for worker in any_of.values():
                yield self.workers.put(worker)
    
    def clients_incoming(self):
        num = 1
        while True:
            yield self.env.timeout(
                rand.expovariate(1/self.av_incoming_time)
            )
            client = Client(self.env, cid=num)
            logging.info(
                f"{self.env.now:.4f}: Client #{client.cid} ARRIVES"
            )

            self.env.process(
                client.get_service(self.workers)
            )

            self.clients.append(client)
            num += 1

    def get_number_of_clients(self):
        return len(self.clients)
    
    def get_number_of_satisfied_clients(self):
        """Каково количество довольных клиентов?"""
        return len([c for c in self.clients if c.satisfied])
    
    def get_number_of_unsatisfied_clients(self):
        """Каково количество недовольных клиентов?"""
        return len(self.clients) - self.get_number_of_satisfied_clients()

    def get_average_waiting_time(self):
        """Каково среднее время ожидания по всем клиентам?"""
        return sum([c.waiting_time for c in self.clients]) / len(self.clients)
    
    def get_average_total_time(self):
        """Каково среднее время нахождения удовлетворённых клиентов в банке?"""
        satisfied = [c.total_time for c in self.clients if c.satisfied]
        return sum(satisfied) / len(satisfied) if satisfied else 0


if __name__ == "__main__":
    rand.seed(42)
    logging.basicConfig(
        level=logging.INFO, filename="bank.log", filemode="w"
    )

    initial_time = 9
    env = sim.Environment(initial_time)
    timed_agenda = [
        [(initial_time, initial_time+2.5), (initial_time+3.5, initial_time+5)],
        [(initial_time+1, initial_time+3.5), (initial_time+4, initial_time+6)]
    ]
    workers = [
        Worker(env, i+1, ta)
        for i, ta in enumerate(timed_agenda)
    ]

    bank = Bank(env, workers)
    bank.operate()
    
    t_sim = 2
    env.run(until=initial_time + t_sim)

    print()
    for w in workers:
        print(
            f"Работник #{w.wid} обслужил клиентов ",
            [c.cid for c in w.clients]
        )

    n_clients = bank.get_number_of_clients()
    n_satisfied = bank.get_number_of_satisfied_clients()
    n_unsatisfied = bank.get_number_of_unsatisfied_clients()

    print("Всего клиентов:\t", n_clients)
    print("Число довольных клиентов:\t", n_satisfied)
    print("Число недовольных клиентов:\t", n_unsatisfied)
    print(
        "Доля довольных клиентов, %:\t",
        round(n_satisfied/n_clients * 100, 2)
    )
    print(
        "Среднее время ожидания, мин:\t",
        round(60 * bank.get_average_waiting_time(), 2)
    )
    print(
        "Среднее время в банке довольных клиентов, мин:\t",
        round(60 * bank.get_average_total_time(), 2)
    )
    print("Текущее время, ч:\t", round(env.now, 2))
