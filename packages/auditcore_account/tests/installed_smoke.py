"""Importprüfung ausschließlich der installierten öffentlichen API."""

from auditcore_account import Actor, AdminService, MemoryRepository, ProfileService, Runtime

runtime = Runtime(MemoryRepository())
account = AdminService(runtime).bootstrap("smoke@example.invalid", "Importprüfung")
assert ProfileService(runtime).read(Actor(account.id, 1), "account", account.id).revision == 1
