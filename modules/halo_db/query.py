from sqlalchemy import and_

from halo_db import get_default_session, Creator, Base
from halo_db.core import Simulation, TimeStep, Halo, HaloProperty


def all_simulations(session=None):
    if session is None:
        session = get_default_session()
    return session.query(Simulation).all()


def all_creators():
    return get_default_session().query(Creator).all()


def get_simulation(id, session=None):
    if session is None:
        session = get_default_session()
    if isinstance(id, str):
        assert "/" not in id
        if "%" in id:
            match_clause = Simulation.basename.like(id)
        else:
            match_clause = Simulation.basename == id
        res = session.query(Simulation).filter(match_clause)
        num = res.count()
        if num == 0:
            raise RuntimeError, "No simulation matches %r" % id
        elif num > 1:
            raise RuntimeError, "Multiple (%d) matches for %r" % (num, id)
        else:
            return res.first()

    else:
        return session.query(Simulation).filter_by(id=id).first()


def get_timestep(id, session=None):
    if session is None:
        session = get_default_session()
    if isinstance(id, str):
        sim, ts = id.split("/")
        sim = get_simulation(sim)
        res = session.query(TimeStep).filter(
            and_(TimeStep.extension.like(ts), TimeStep.simulation_id == sim.id))
        num = res.count()
        if num == 0:
            raise RuntimeError, "No timestep matches for %r" % id
        elif num > 1:
            raise RuntimeError, "Multiple (%d) matches for timestep %r of simulation %r" % (
                num, ts, sim)
        else:
            return res.first()
    else:
        return session.query(TimeStep).filter_by(id=id).first()


def get_halo(id, session=None):
    """Get a halo from an ID or an identifying string

    Optionally, use the specified session.

    :rtype: Halo
    """
    if session is None:
        session = get_default_session()
    if isinstance(id, str):
        sim, ts, halo = id.split("/")
        ts = get_timestep(sim + "/" + ts)
        if "." in halo:
            halo_type, halo_number = map(int, halo.split("."))
        else:
            halo_type, halo_number = 0, int(halo)
        return session.query(Halo).filter_by(timestep_id=ts.id, halo_number=halo_number, halo_type=halo_type).first()
    return session.query(Halo).filter_by(id=id).first()


def get_item(path, session=None):
    c = path.count("/")
    if c is 0:
        return get_simulation(path, session)
    elif c is 1:
        return get_timestep(path, session)
    elif c is 2:
        return get_halo(path, session)


def get_haloproperty(id):
    return get_default_session().query(HaloProperty).filter_by(id=id).first()


def get_items(path_list, session=None):
    return [get_item(path,session) for path in path_list]


def getdb(cl) :
    """Function decorator to ensure input is parsed into a database object."""
    def getdb_inner(f) :
        def wrapped(*args, **kwargs) :

            if not isinstance(args[0], Base) :
                args = list(args)
                if isinstance(args[0], int) :
                    item = get_default_session().query(cl).filter_by(id=args[0]).first()
                else :
                    item = get_item(args[0])
                if not isinstance(item, cl) :
                    if isinstance(item, Simulation) and cl is Halo:
                        print "Picking first timestep and first halo"
                        item = item.timesteps[0].halos[0]
                    else :
                        raise RuntimeError, "Path points to wrong type of db object %r"%item
                args[0] = item
            return f(*args,**kwargs)
        return wrapped
    return getdb_inner


__all__ = ['all_simulations', 'all_creators', 'get_simulation', 'get_timestep',
           'get_halo', 'get_item' ,'get_haloproperty', 'get_items', 'getdb']