from types import SimpleNamespace
from pathlib import Path
import pytest
from app import create_app, db
from config import ProductionConfig


def settings(monkeypatch, tmp_path):
    monkeypatch.setattr(ProductionConfig, 'SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'app.db'))
    monkeypatch.setattr(ProductionConfig, 'DATA_DIR', str(tmp_path / 'data'))
    static = tmp_path / 'static'
    (static / 'img').mkdir(parents=True)
    return SimpleNamespace(config={'SECRET_KEY': 'x' * 64}, static_folder=str(static))


@pytest.mark.parametrize('secret', ['', 'short', 'replace-with-a-random-private-secret'])
def test_production_rejects_missing_secret(monkeypatch, tmp_path, secret):
    app = settings(monkeypatch, tmp_path)
    app.config['SECRET_KEY'] = secret
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        ProductionConfig.init_app(app)


def test_production_rejects_missing_database(monkeypatch, tmp_path):
    app = settings(monkeypatch, tmp_path)
    monkeypatch.setattr(ProductionConfig, 'SQLALCHEMY_DATABASE_URI', None)
    with pytest.raises(RuntimeError, match='PRODUCTION_DATABASE_URL'):
        ProductionConfig.init_app(app)


def test_production_requires_absolute_storage(monkeypatch, tmp_path):
    app = settings(monkeypatch, tmp_path)
    monkeypatch.setattr(ProductionConfig, 'DATA_DIR', 'relative')
    with pytest.raises(RuntimeError, match='absolute'):
        ProductionConfig.init_app(app)


def test_images_survive_release_directory_change(monkeypatch, tmp_path):
    app = settings(monkeypatch, tmp_path)
    ProductionConfig.init_app(app)
    picture = Path(app.config['EDITORS_UPLOAD_PATH']) / 'example.png'
    picture.write_bytes(b'test image')
    fresh = tmp_path / 'new-release' / 'static'
    (fresh / 'img').mkdir(parents=True)
    app.static_folder = str(fresh)
    ProductionConfig.init_app(app)
    assert (fresh / 'img/editors/example.png').read_bytes() == b'test image'
    ProductionConfig.init_app(app)


def test_existing_images_are_not_overwritten(monkeypatch, tmp_path):
    app = settings(monkeypatch, tmp_path)
    folder = Path(app.static_folder) / 'img/editors'
    folder.mkdir()
    (folder / 'old.png').write_bytes(b'keep')
    with pytest.raises(RuntimeError, match='Move existing'):
        ProductionConfig.init_app(app)
    assert (folder / 'old.png').read_bytes() == b'keep'


def test_readiness_endpoint(monkeypatch):
    app = create_app('testing')
    with app.test_client() as client:
        assert client.get('/healthz').json == {'status': 'ok'}
        def unavailable(*args, **kwargs):
            raise RuntimeError('private connection detail')
        monkeypatch.setattr(db.session, 'execute', unavailable)
        result = client.get('/healthz')
        assert result.status_code == 503
        assert result.json == {'status': 'unavailable'}
        assert 'private connection detail' not in result.text
