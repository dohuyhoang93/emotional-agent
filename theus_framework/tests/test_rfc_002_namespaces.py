import pytest
import asyncio
from theus.engine import TheusEngine
from theus.contracts import process, AdminTransaction
from theus.context import NamespacePolicy, NamespaceRegistry

# --- Processes ---

@process(inputs=["trading.balance"])
async def p_read_trading(ctx):
    # This should succeed if allow_read=True
    return ctx["trading"]["balance"]

@process(outputs=["trading.balance"])
async def p_write_trading(ctx, new_balance):
    # This should fail if allow_update=False
    ctx.trading.balance = new_balance

@process(inputs=["default.key"])
async def p_read_default(ctx):
    return ctx.key # Default namespace is merged at root

# --- Tests ---

@pytest.mark.asyncio
async def test_namespace_isolation_and_policy():
    # 0. Clean Registry (Singleton safety)
    NamespaceRegistry().clear()
    
    # 1. Setup Namespaces
    # 'trading' has restricted update policy
    trading_policy = NamespacePolicy(allow_read=True, allow_update=False, allow_append=False)
    
    engine = TheusEngine(
        context={"key": "val"},
        namespaces=[
            {"name": "trading", "policy": trading_policy, "data": {"balance": 1000}}
        ]
    )

    # 2. Verify Hydration
    print(f"\nDEBUG: Initial Data={engine._namespaces.get_all_data()}")
    assert engine._namespaces.get_policy("trading").allow_update == False
    
    # 3. Test Read (Allowed)
    balance = await engine.execute(p_read_trading)
    print(f"DEBUG: Read balance={balance}")
    assert balance == 1000

    # 4. Test Write (Blocked by Python-side Guard filter)
    # The guard should have stripped 'trading.balance' from allowed_outputs
    try:
        await engine.execute(p_write_trading, 2000)
        # If it reaches here, it means the write happened (Incorrect)
        assert False, "Write to restricted Namespace should have failed"
    except PermissionError as e:
        assert "Illegal" in str(e)
        # Verify state didn't change
        assert engine._namespaces._namespaces["trading"]["data"]["balance"] == 1000

@pytest.mark.asyncio
async def test_cross_namespace_isolation():
    NamespaceRegistry().clear()
    
    engine = TheusEngine(
        namespaces=[
            {"name": "internal", "data": {"secret": "123"}},
            {"name": "public", "data": {"info": "abc"}}
        ]
    )

    @process(inputs=["public.info"])
    async def p_public_only(ctx):
        # Should not see 'internal'
        try:
            return ctx.internal.secret
        except (AttributeError, PermissionError):
            return "hidden"

    result = await engine.execute(p_public_only)
    assert result == "hidden"

@pytest.mark.asyncio
async def test_admin_bypass_namespace():
    NamespaceRegistry().clear()
    
    trading_policy = NamespacePolicy(allow_update=False)
    engine = TheusEngine(
        namespaces=[
            {"name": "trading", "policy": trading_policy, "data": {"balance": 1000}}
        ]
    )

    @process(outputs=["trading.balance"])
    async def p_admin_fix(ctx):
        with AdminTransaction(ctx) as admin:
            admin.trading.balance = 5000

    # Execute with Admin Bypass
    await engine.execute(p_admin_fix)
    
    # Verify state changed (Admin Bypass works on Namespace)
    assert engine._namespaces._namespaces["trading"]["data"]["balance"] == 5000

if __name__ == "__main__":
    pytest.main([__file__])
