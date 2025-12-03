from pathlib import Path
import unittest
from rich.console import Console
from rich.table import Table
from rich.traceback import Traceback
from rich.panel import Panel
from rich.text import Text

console = Console()


# ============================================================
#   RESULTADO PERSONALIZADO
# ============================================================
class RichTestResult(unittest.TestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_files = {}  # mapa: archivo -> lista de tests (name, result)

    def _register_test(self, test, status):
        """Guardar resultados por archivo para el resumen final."""
        file = Path(test.__class__.__module__.replace(".", "/")).name + ".py"
        if file not in self.test_files:
            self.test_files[file] = []
        self.test_files[file].append((test._testMethodName, status))

    def startTest(self, test):
        super().startTest(test)
        name = test._testMethodName
        cls = test.__class__.__name__
        console.print(f"[cyan]→ {cls}::{name}[/cyan]")

    def addSuccess(self, test):
        super().addSuccess(test)
        console.print("   [green]✔ OK[/green]")
        self._register_test(test, "OK")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        console.print("   [red]✖ FAIL[/red]")

        tb = Traceback.from_exception(err[0], err[1], err[2])
        console.print(Panel(tb, title="[bold red]FAIL[/bold red]", border_style="red"))

        self._register_test(test, "FAIL")

    def addError(self, test, err):
        super().addError(test, err)
        console.print("   [bold red]⚠ ERROR[/bold red]")

        tb = Traceback.from_exception(err[0], err[1], err[2])
        console.print(Panel(tb, title="[bold red]ERROR[/bold red]", border_style="red"))

        self._register_test(test, "ERROR")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        console.print(f"   [yellow]→ SKIPPED[/yellow]  ({reason})")

        self._register_test(test, "SKIPPED")


# ============================================================
#   RUNNER PERSONALIZADO
# ============================================================
class RichTestRunner(unittest.TextTestRunner):
    resultclass = RichTestResult

    def run(self, test):
        console.rule("[bold green] EJECUTANDO TESTS [/bold green]")

        result = super().run(test)

        console.rule("[bold blue] RESUMEN DETALLADO [/bold blue]")

        # ----------------------------------------------------
        #   Tabla por archivo
        # ----------------------------------------------------
        for file, tests in result.test_files.items():
            table = Table(title=f"Archivo: [magenta]{file}[/magenta]", expand=False)

            table.add_column("Test", justify="left")
            table.add_column("Resultado", justify="center")

            for name, status in tests:
                color = {
                    "OK": "green",
                    "FAIL": "red",
                    "ERROR": "bold red",
                    "SKIPPED": "yellow",
                }[status]
                table.add_row(name, f"[{color}]{status}[/{color}]")

            console.print(table)

        # ----------------------------------------------------
        #   Resumen global compacto
        # ----------------------------------------------------
        console.rule("[bold yellow] RESUMEN GLOBAL [/bold yellow]")

        glob = Table(box=None, expand=False)
        glob.add_column("Resultado")
        glob.add_column("Cantidad", justify="right")

        ok = (
            result.testsRun
            - len(result.failures)
            - len(result.errors)
            - len(result.skipped)
        )
        glob.add_row("[green]OK[/green]", str(ok))
        glob.add_row("[red]FAIL[/red]", str(len(result.failures)))
        glob.add_row("[bold red]ERROR[/bold red]", str(len(result.errors)))
        glob.add_row("[yellow]→ SKIPPED[/yellow]", str(len(result.skipped)))

        console.print(glob)

        # Mensaje final
        if result.failures or result.errors:
            console.print(
                Panel(
                    "[bold red]Hay fallos en los tests[/bold red]", border_style="red"
                )
            )
        else:
            console.print(
                Panel(
                    "[bold green]✔ Todos los tests pasaron correctamente[/bold green]",
                    border_style="green",
                )
            )

        return result


# ============================================================
#   ENTRY POINT
# ============================================================
def main():
    loader = unittest.TestLoader()
    tests_path = Path(__file__).parent / "tests"
    suite = loader.discover(str(tests_path))

    runner = RichTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == "__main__":
    main()
