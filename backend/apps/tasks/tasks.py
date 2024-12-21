import os
import sys
import json
import psutil
import nbformat
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import TaskExecution

@shared_task(bind=True)
def execute_task(self, execution_id):
    """
    Ejecuta una tarea y actualiza su estado
    """
    execution = TaskExecution.objects.get(id=execution_id)
    version = execution.task_version

    try:
        # Actualizar estado a running
        execution.status = 'running'
        execution.started_at = timezone.now()
        execution.save()

        # Preparar entorno de ejecución
        working_dir = os.path.join(settings.MEDIA_ROOT, 'executions', str(execution.id))
        os.makedirs(working_dir, exist_ok=True)

        # Copiar archivo al directorio de trabajo
        file_path = os.path.join(working_dir, os.path.basename(version.file.name))
        with open(file_path, 'wb') as f:
            f.write(version.file.read())

        # Instalar dependencias si existen
        if version.requirements:
            os.system(f'pip install -r {version.requirements}')

        # Ejecutar el archivo según su tipo
        if file_path.endswith('.py'):
            result = execute_python_file(file_path, execution)
        elif file_path.endswith('.ipynb'):
            result = execute_notebook(file_path, execution)

        # Actualizar estado final
        execution.status = 'completed'
        execution.completed_at = timezone.now()
        execution.save()

        return result

    except Exception as e:
        execution.status = 'failed'
        execution.error_message = str(e)
        execution.completed_at = timezone.now()
        execution.save()
        raise

def execute_python_file(file_path, execution):
    """
    Ejecuta un archivo Python y captura su salida
    """
    # Redirigir stdout y stderr
    from io import StringIO
    import contextlib

    output = StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            # Monitorear recursos
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

            # Ejecutar archivo
            with open(file_path) as f:
                exec(f.read())

            # Calcular uso de recursos
            final_memory = process.memory_info().rss
            memory_used = final_memory - initial_memory
            cpu_percent = process.cpu_percent()

            execution.metrics = {
                'memory_used': memory_used,
                'cpu_percent': cpu_percent
            }
            execution.logs = output.getvalue()
            execution.save()

            return {
                'success': True,
                'output': output.getvalue()
            }

        except Exception as e:
            execution.error_message = str(e)
            execution.logs = output.getvalue()
            execution.save()
            raise

def execute_notebook(file_path, execution):
    """
    Ejecuta un notebook Jupyter
    """
    try:
        import nbformat
        from nbconvert.preprocessors import ExecutePreprocessor

        with open(file_path) as f:
            nb = nbformat.read(f, as_version=4)

        # Configurar el ejecutor
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

        # Ejecutar el notebook
        ep.preprocess(nb, {'metadata': {'path': os.path.dirname(file_path)}})

        # Guardar resultados
        output_path = file_path.replace('.ipynb', '_output.ipynb')
        with open(output_path, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)

        # Extraer resultados
        outputs = []
        for cell in nb.cells:
            if cell.cell_type == 'code' and hasattr(cell, 'outputs'):
                outputs.extend(cell.outputs)

        execution.logs = json.dumps(outputs)
        execution.save()

        return {
            'success': True,
            'notebook_output': output_path
        }

    except Exception as e:
        execution.error_message = str(e)
        execution.save()
        raise 