"""
Non-autonomous dynamic systems.

# TODO: debug SEIR model
# TODO: Tank - probably not working properly


"""
import numpy as np
from scipy.integrate import odeint

# local imports
from slip.emulator import ODE_NonAutonomous


class SEIR_population(ODE_NonAutonomous):
    """
    Susceptible, Exposed, Infected, and Recovered (SEIR) population population model
    COVID19 spread
    source of the model:
    https://apmonitor.com/do/index.php/Main/COVID-19Response

    states:
    Susceptible (s): population fraction that is susceptible to the virus
    Exposed (e): population fraction is infected with the virus but does not transmit to others
    Infectious (i): population fraction that is infected and can infect others
    Recovered (r): population fraction recovered from infection and is immune from further infection
    """

    def parameters(self):
        self.N = 10000 # population
        # initial number of infected and recovered individuals
        self.e_0 = 1 / self.N
        self.i_0 = 0.00
        self.r_0 = 0.00
        self.s_0 = 1 - self.e_0 - self.i_0 - self.r_0
        self.x0 = np.asarray([self.s_0, self.e_0, self.i_0, self.r_0])

        self.nx = 4
        self.nu = 1

        self.t_incubation = 5.1
        self.t_infective = 3.3
        self.R0 = 2.4
        self.alpha = 1 / self.t_incubation
        self.gamma = 1 / self.t_infective
        self.beta = self.R0 * self.gamma

    def equations(self, x, t, u):
        # Inputs (1): social distancing (u=0 (none), u=1 (total isolation))
        # States (4):
        # Susceptible (s): population fraction that is susceptible to the virus
        # Exposed (e): population fraction is infected with the virus but does not transmit to others
        # Infectious (i): population fraction that is infected and can infect others
        # Recovered (r): population fraction recovered from infection and is immune from further infection
        s = x[0]
        e = x[1]
        i = x[2]
        r = x[3]
        # SEIR equations
        sdt = -(1 - u) * self.beta * s * i,
        edt = (1 - u) * self.beta * s * i - self.alpha * e,
        idt = self.alpha * e - self.gamma * i,
        rdt = self.gamma * i
        dx = [sdt, edt, idt, rdt]
        return dx

    def simulate(self, ninit, nsim, ts, U, x0=None):
        """
        :param nsim: (int) Number of steps for open loop response
        :param ninit: (float) initial simulation time
        :param ts: (float) step size, sampling time
        :param U: (float) control input vector (social distancing)
        :param x0: (float) state initial conditions
        :param x: (ndarray, shape=(self.nx)) states (SEIR)
        :return: The response matrices, i.e. X
        """
        # initial conditions states + uncontrolled inputs
        if x0 is None:
            x = self.x0
        else:
            assert x0.shape[0] == self.nx, "Mismatch in x0 size"
            x = x0

        # alpha = 1 / self.t_incubation
        # gamma = 1 / self.t_infective
        # beta = self.R0 * self.gamma

        # time interval
        t = np.arange(0, nsim) * ts + ninit
        X = []
        N = 0
        for u in U:
            dT = [t[N], t[N + 1]]
            # TODO: error here
            xdot = odeint(self.equations, x, dT, args=(u,))
            # xdot = odeint(self.equations, x, dT,
            #               args=(u, alpha, beta, gamma))
            x = xdot[-1]
            X.append(x)  # updated states trajectories
            N += 1
            if N == nsim:
                break
        return np.asarray(X)


class Tank(ODE_NonAutonomous):
    """
    Single Tank model
    original code obtained from APMonitor:
    https://apmonitor.com/pdc/index.php/Main/TankLevel
    """

    def parameters(self):
        self.rho = 1000.0  # water density (kg/m^3)
        self.A = 1.0  # tank area (m^2)
        self.c1 = 80.0  # inlet valve coefficient (kg/s / %open)
        self.c2 = 40.0  # outlet valve coefficient (kg/s / %open)
        # Initial Conditions for the States
        self.x0 = 0
        # initial valve position
        self.u0 = 10

    def equations(self, x, t, pump, valve):
        # States (1): level in the tanks
        # Inputs (1): valve
        # equations
        dx_dt = (self.c1/(self.rho*self.A)) *(1.0 - valve) * pump - self.c2 * np.sqrt(x)
        if x >= 1.0 and dx_dt > 0.0:
            dx_dt = 0
        return dx_dt

    def simulate(self, ninit, nsim, ts, Pump, Valve, x0=None):
        """
        :param nsim: (int) Number of steps for open loop response
        :param ninit: (float) initial simulation time
        :param ts: (float) step size, sampling time
        :param Valve: (float) control input vector
        :param x0: (float) state initial conditions
        :param x: (ndarray, shape=(self.nx)) states
        :return: The response matrices, i.e. X
        """
        # initial conditions states + uncontrolled inputs
        if x0 is None:
            x = self.x0
        else:
            assert x0.shape[0] == self.nx, "Mismatch in x0 size"
            x = x0
        # time interval
        t = np.arange(0, nsim) * ts + ninit
        X = []
        N = 0
        for pump, valve in zip(Pump, Valve):
            u = (pump, valve)
            dT = [t[N], t[N + 1]]
            xdot = odeint(self.equations, x, dT, args=u)
            x = xdot[-1]
            X.append(x)  # updated states trajectories
            N += 1
            if N == nsim:
                break
        return np.asarray(X)


class TwoTank(ODE_NonAutonomous):
    """
    Two Tank model
    original code obtained from APMonitor:
    https://apmonitor.com/do/index.php/Main/LevelControl
    """

    def parameters(self):
        super().parameters()
        self.c1 = 0.08  # inlet valve coefficient
        self.c2 = 0.04  # tank outlet coefficient
        # Initial Conditions for the States
        self.x0 = np.asarray([0, 0])
        # default simulation setup
        pump = np.empty((self.nsim - 1))
        pump[0] = 0
        pump[1:501] = 0.5
        pump[251:551] = 0.1
        pump[551: self.nsim - 1] = 0.2
        valve = np.zeros((self.nsim - 1))
        self.U = np.vstack([pump, valve]).T
        self.nu = 2
        self.nx = 2

    def equations(self, x, t, u):
        # States (2): level in the tanks
        h1 = x[0]
        h2 = x[1]
        # Inputs (2): pump and valve
        pump = u[0]
        valve = u[1]
        # equations
        dhdt1 = self.c1 * (1.0 - valve) * pump - self.c2 * np.sqrt(h1)
        dhdt2 = self.c1 * valve * pump + self.c2 * np.sqrt(h1) - self.c2 * np.sqrt(h2)
        if h1 >= 1.0 and dhdt1 > 0.0:
            dhdt1 = 0
        if h2 >= 1.0 and dhdt2 > 0.0:
            dhdt2 = 0
        dhdt = [dhdt1, dhdt2]
        return dhdt


class CSTR(ODE_NonAutonomous):
    """
    CSTR model
    original code obtained from APMonitor:
    http://apmonitor.com/do/index.php/Main/NonlinearControl
    """

    def parameters(self):
        # Volumetric Flowrate (m^3/sec)
        self.q = 100
        # Volume of CSTR (m^3)
        self.V = 100
        # Density of A-B Mixture (kg/m^3)
        self.rho = 1000
        # Heat capacity of A-B Mixture (J/kg-K)
        self.Cp = 0.239
        # Heat of reaction for A->B (J/mol)
        self.mdelH = 5e4
        # E - Activation energy in the Arrhenius Equation (J/mol)
        # R - Universal Gas Constant = 8.31451 J/mol-K
        self.EoverR = 8750
        # Pre-exponential factor (1/sec)
        self.k0 = 7.2e10
        # U - Overall Heat Transfer Coefficient (W/m^2-K)
        # A - Area - this value is specific for the U calculation (m^2)
        self.UA = 5e4
        # Steady State Initial Conditions for the States
        self.Ca_ss = 0.87725294608097
        self.T_ss = 324.475443431599
        self.x0 = np.empty(2)
        self.x0[0] = self.Ca_ss
        self.x0[1] = self.T_ss
        # Steady State Initial Condition for the Uncontrolled Inputs
        self.u_ss = 300.0 # cooling jacket Temperature (K)
        self.Tf = 350 # Feed Temperature (K)
        self.Caf = 1 # Feed Concentration (mol/m^3)
        # dimensions
        self.nx = 2
        self.nu = 1
        self.nd = 2
        # default simulation setup
        # Step cooling temperature to 295
        u_ss = 300.0
        U = np.ones(self.nsim - 1) * u_ss
        U[50:150] = 303.0
        U[150:250] = 297.0
        U[250:350] = 295.0
        U[350:450] = 298.0
        U[450:550] = 298.0
        U[650:750] = 303.0
        U[750:850] = 306.0
        U[850:] = 300.0
        self.U = U.reshape(-1, 1)

    def equations(self, x, t, u):
        # Inputs (1):
        # Temperature of cooling jacket (K)
        Tc = u
        # Disturbances (2):
        # Tf = Feed Temperature (K)
        # Caf = Feed Concentration (mol/m^3)
        # States (2):
        # Concentration of A in CSTR (mol/m^3)
        Ca = x[0]
        # Temperature in CSTR (K)
        T = x[1]

        # reaction rate
        rA = self.k0 * np.exp(-self.EoverR / T) * Ca
        # Calculate concentration derivative
        dCadt = self.q / self.V * (self.Caf - Ca) - rA
        # Calculate temperature derivative
        dTdt = self.q / self.V * (self.Tf - T) \
               + self.mdelH / (self.rho * self.Cp) * rA \
               + self.UA / self.V / self.rho / self.Cp * (Tc - T)
        xdot = np.zeros(2)
        xdot[0] = dCadt
        xdot[1] = dTdt
        return xdot

"""
Chaotic nonlinear ODEs 

https://en.wikipedia.org/wiki/List_of_chaotic_maps
"""


class HindmarshRose(ODE_NonAutonomous):
    """
    Hindmarsh–Rose model of neuronal activity
    https://en.wikipedia.org/wiki/Hindmarsh%E2%80%93Rose_model
    https://demonstrations.wolfram.com/HindmarshRoseNeuronModel/
    """

    def parameters(self):
        super().parameters()
        self.a = 1
        self.b = 2.6
        self.c = 1
        self.d = 5
        self.s = 4
        self.xR = -8/5
        self.r = 0.01
        self.umin = -10
        self.umax = 10
        self.x0 = np.asarray([-5,-10,0])
        # default simulation setup
        self.nsim = 5001
        self.U = 3 * np.asarray([np.ones((self.nsim - 1))]).T
        self.nu = 1
        self.nx = 3

    def equations(self, x, t, u):
        # Derivatives
        theta = -self.a*x[0]**3 + self.b*x[0]**2
        phi = self.c -self.d*x[0]**2
        dx1 = x[1] + theta - x[2] + u
        dx2 = phi - x[1]
        dx3 = self.r*(self.s*(x[0]-self.xR)-x[2])
        dx = [dx1, dx2, dx3]
        return dx


