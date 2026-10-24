import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../auth/AuthContext';
import { vendorApi } from '../../api/endpoints';
import { useRequest } from '../../api/useRequest';
import { Notice } from '../../Components/Notice';

const BLANK = { name: '', description: '', price: '' };

export function Menu() {
  const { credentials } = useAuth();
  const { run: loadMenu, error: menuError } = useRequest();
  const { run: loadStall, error: stallError } = useRequest();
  const { run: change, pending: changing, error: changeError } = useRequest();

  const [items, setItems] = useState([]);
  const [stall, setStall] = useState(null);
  const [draft, setDraft] = useState(BLANK);

  const refresh = useCallback(() => {
    loadMenu(() => vendorApi.menu(credentials)).then((d) => { if (d) setItems(d.items); });
    loadStall(() => vendorApi.stall(credentials)).then((d) => { if (d) setStall(d); });
  }, [loadMenu, loadStall, credentials]);
  useEffect(() => { refresh(); }, [refresh]);

  async function addItem(event) {
    event.preventDefault();
    const created = await change(() => vendorApi.addItem(credentials, {
      name: draft.name.trim(),
      description: draft.description.trim(),
      price: Number(draft.price),
    }));
    if (created) { setDraft(BLANK); refresh(); }
  }

  async function editPrice(item) {
    const entered = window.prompt(`New price for ${item.name}`, item.price.toFixed(2));
    if (entered === null) return;
    const updated = await change(() =>
      vendorApi.editItem(credentials, item.id, { price: Number(entered) }));
    if (updated) refresh();
  }

  async function toggleItem(item) {
    const updated = await change(() =>
      vendorApi.setAvailability(credentials, item.id, !item.available));
    if (updated) refresh();
  }

  async function toggleStall() {
    const updated = await change(() =>
      vendorApi.setTrading(credentials, !stall.is_accepting_orders));
    if (updated) refresh();
  }

  return (
    <>
      <Notice error={menuError || stallError || changeError} />
      
      {stall && (
        <div className="d-flex justify-content-between align-items-center mb-3">
          <div>
            <h2 className="h5 mb-0">{stall.stall_name}</h2>
            <small className="text-muted">
              {stall.is_accepting_orders ? 'Taking orders' : 'Not taking orders'}
            </small>
          </div>
          <button className={`btn btn-sm ${stall.is_accepting_orders
                    ? 'btn-outline-danger' : 'btn-outline-success'}`}
                  onClick={toggleStall} disabled={changing}>
            {stall.is_accepting_orders ? 'Close stall' : 'Open stall'}
          </button>
        </div>
      )}

      <ul className="list-group mb-4">
        {items.map((item) => (
          <li className="list-group-item d-flex justify-content-between align-items-center"
              key={item.id}>
            <div>
              <div className="fw-semibold">
                {item.name}{' '}
                {!item.available && <span className="badge text-bg-secondary">Sold out</span>}
              </div>
              <div className="small text-muted">
                {item.description} · ${item.price.toFixed(2)}
              </div>
            </div>
            <div className="d-flex gap-2">
              <button className="btn btn-outline-secondary btn-sm"
                      onClick={() => editPrice(item)} disabled={changing}>
                Edit price
              </button>
              <button className="btn btn-outline-secondary btn-sm"
                      onClick={() => toggleItem(item)} disabled={changing}>
                {item.available ? 'Mark sold out' : 'Back in stock'}
              </button>
            </div>
          </li>
        ))}
      </ul>

      <h3 className="h6">Add an item</h3>
      <form className="row g-2 align-items-end" onSubmit={addItem}>
        <div className="col-md-4">
          <label className="form-label small" htmlFor="name">Name</label>
          <input id="name" className="form-control form-control-sm" required
                 value={draft.name}
                 onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
        </div>
        <div className="col-md-5">
          <label className="form-label small" htmlFor="description">Description</label>
          <input id="description" className="form-control form-control-sm"
                 value={draft.description}
                 onChange={(e) => setDraft({ ...draft, description: e.target.value })} />
        </div>
        <div className="col-md-2">
          <label className="form-label small" htmlFor="price">Price</label>
          <input id="price" className="form-control form-control-sm" type="number"
                 step="0.01" min="0.01" required value={draft.price}
                 onChange={(e) => setDraft({ ...draft, price: e.target.value })} />
        </div>
        <div className="col-md-1">
          <button className="btn btn-primary btn-sm w-100" type="submit" disabled={changing}>
            Add
          </button>
        </div>
      </form>
    </>
  );
}