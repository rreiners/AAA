import subprocess
import yaml
import datetime
from astral import LocationInfo
import matplotlib.pyplot as plt
from pathlib import Path
from dotmap import DotMap


class StyleManager:
    def __init__(self, config_path=None):
        # Get project root directory (two levels up from this file)
        self.project_root = Path(__file__).parents[2]

        if config_path is None:
            config_path = self.project_root / "config" / "styling.yaml"

        self.config_path = config_path
        self.config = self.load_config()
        self.apply_style()
        self.configure_jupyter_plotting()

    def configure_jupyter_plotting(self):
        """Configure Jupyter notebook plotting settings."""
        try:
            from IPython import get_ipython

            ipython = get_ipython()
            if ipython is not None:
                # Configure inline plotting
                ipython.run_line_magic("matplotlib", "inline")

                # Set figure formats
                ipython.run_line_magic(
                    "config", "InlineBackend.figure_formats = ['svg']"
                )
                ipython.run_line_magic(
                    "config", "InlineBackend.figure_format = 'retina'"
                )

                # Optional: Set additional configurations
                ipython.run_line_magic(
                    "config",
                    "InlineBackend.print_figure_kwargs = {'bbox_inches': 'tight'}",
                )
        except ImportError:
            # Not running in Jupyter/IPython environment
            pass

    @staticmethod
    def check_macos_theme():
        try:
            # Try to get the system's appearance setting
            result = subprocess.check_output(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            return "dark" if "Dark" in result else "light"

        except FileNotFoundError:
            try:
                with open("/proc/version", "r") as f:
                    version_info = f.read().lower()
                    if "microsoft" in version_info:
                        return "dark"
                    else:
                        raise Exception("Not MacOS or WSL")
            except Exception:
                from astral.sun import sun

                # city = LocationInfo("Berlin", "Germany", "Europe/Berlin", 52.52, 13.4050)
                # city is poerto de la cruz on tenerife
                city = LocationInfo(
                    "Puerto de la Cruz",
                    "Spain",
                    "Atlantic/Canary",
                    28.4167,
                    -16.55,
                )
                sun = sun(city.observer, date=datetime.datetime.today())
                current_time = datetime.datetime.now(datetime.timezone.utc)
                style = (
                    "light"
                    if sun["sunrise"] < current_time < sun["sunset"]
                    else "dark"
                )
                return style

    def load_config(self):
        with open(self.config_path, "r") as file:
            config = yaml.safe_load(file)

        styling = self.check_macos_theme()

        # Apply theme-specific settings
        theme_config = config["themes"][styling]

        # Construct final configuration
        final_config = {
            **config["default"],
            **config["plotting"],
            **theme_config,
            "styling": styling,
        }

        return DotMap(final_config)

    def apply_style(self):
        """Apply the styling configuration to matplotlib."""
        plt.style.use(self.config.plt_style)
        plt.rcParams.update(
            {
                "font.size": self.config.font_size,
                "font.family": self.config.font_family,
                "figure.facecolor": self.config.background,
                "figure.figsize": (self.config.width, self.config.height),
                "axes.facecolor": self.config.background,
                "axes.edgecolor": self.config.contour_color,
                "axes.labelcolor": self.config.contour_color,
                "axes.titlecolor": self.config.contour_color,
                "legend.labelcolor": self.config.contour_color,
                "xtick.color": self.config.contour_color,
                "ytick.color": self.config.contour_color,
                "axes.prop_cycle": plt.cycler(
                    color=[
                        self.config.plot_color,
                        self.config.second_plot_color,
                        "#009E73",
                        "#0072B2",
                        "#D55E00",
                        "#56B4E9",
                        "#CC79A7",
                        "#F0E442",
                    ]
                ),
            }
        )

    def style_axis(self, ax):
        """Apply styling to a matplotlib axis."""
        ax.set_facecolor(self.config.background)
        ax.spines["bottom"].set_color(self.config.contour_color)
        ax.spines["top"].set_color(self.config.contour_color)
        ax.spines["right"].set_color(self.config.contour_color)
        ax.spines["left"].set_color(self.config.contour_color)
        ax.tick_params(colors=self.config.contour_color)
        ax.xaxis.label.set_color(self.config.contour_color)
        ax.yaxis.label.set_color(self.config.contour_color)
        return ax


# Create a global style manager instance
style_manager = StyleManager()
