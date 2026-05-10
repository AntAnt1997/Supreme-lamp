import { useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";

type Task = {
  id: number;
  title: string;
  done: boolean;
};

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [input, setInput] = useState("");
  const [showCompleted, setShowCompleted] = useState(true);
  const nextTaskId = useRef(1);

  const visibleTasks = useMemo(() => {
    if (showCompleted) return tasks;
    return tasks.filter((task) => !task.done);
  }, [showCompleted, tasks]);

  const completedCount = useMemo(
    () => tasks.filter((task) => task.done).length,
    [tasks],
  );

  const addTask = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const title = input.trim();
    if (!title) return;
    const taskId = nextTaskId.current;
    nextTaskId.current += 1;

    setTasks((current) => [
      { id: taskId, title, done: false },
      ...current,
    ]);
    setInput("");
  };

  const toggleTask = (id: number) => {
    setTasks((current) =>
      current.map((task) =>
        task.id === id ? { ...task, done: !task.done } : task,
      ),
    );
  };

  const removeTask = (id: number) => {
    setTasks((current) => current.filter((task) => task.id !== id));
  };

  const emptyStateMessage =
    tasks.length > 0 && !showCompleted && visibleTasks.length === 0
      ? 'All tasks are completed. Turn on "Show completed" to view them.'
      : "No tasks yet. Add one above to get started.";

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <main className="mx-auto flex w-full max-w-2xl flex-col gap-6 px-4 py-10">
        <header className="space-y-2">
          <h1 className="text-3xl font-bold">Simple Task App</h1>
          <p className="text-sm text-gray-300">
            A small app to add, complete, and remove tasks.
          </p>
        </header>

        <form onSubmit={addTask} className="flex gap-2">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Add a new task"
            className="flex-1 rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm outline-none ring-emerald-500 placeholder:text-gray-500 focus:ring-2"
          />
          <button
            type="submit"
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold hover:bg-emerald-500"
          >
            Add
          </button>
        </form>

        <div className="flex items-center justify-between text-sm text-gray-300">
          <p>
            {completedCount} / {tasks.length} completed
          </p>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showCompleted}
              onChange={(event) => setShowCompleted(event.target.checked)}
            />
            Show completed
          </label>
        </div>

        <ul className="space-y-2">
          {visibleTasks.map((task) => (
            <li
              key={task.id}
              className="flex items-center justify-between rounded-md border border-gray-800 bg-gray-900 px-3 py-2"
            >
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={task.done}
                  onChange={() => toggleTask(task.id)}
                />
                <span className={task.done ? "text-gray-500 line-through" : ""}>
                  {task.title}
                </span>
              </label>
              <button
                type="button"
                onClick={() => removeTask(task.id)}
                className="rounded-md border border-gray-700 px-2 py-1 text-xs hover:bg-gray-800"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>

        {visibleTasks.length === 0 && (
          <p className="rounded-md border border-dashed border-gray-700 p-4 text-center text-sm text-gray-400">
            {emptyStateMessage}
          </p>
        )}
      </main>
    </div>
  );
}
