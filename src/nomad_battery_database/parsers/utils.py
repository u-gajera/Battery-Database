import json
from typing import Optional

from nomad.datamodel.context import ClientContext
from nomad.utils import hash as _hash


def get_reference(upload_id: str, entry_id: str) -> str:
    return f'../uploads/{upload_id}/archive/{entry_id}#data'


def get_entry_id_from_file_name(file_name: str, archive) -> str:
    return _hash(archive.metadata.upload_id, file_name)


def create_archive(section, parent_archive, file_name: str) -> Optional[str]:
    """
    Write *section* to ``file_name`` inside the current upload and register it
    as a **child archive**.  Returns a reference string that can be stored in
    relationships if you need it later.
    """
    # Uploads created via the REST client do not expose a raw-file context
    if isinstance(parent_archive.m_context, ClientContext):
        return None

    # Only write once (idempotent re-upload)
    if not parent_archive.m_context.raw_path_exists(file_name):
        with parent_archive.m_context.raw_file(file_name, 'w') as fp:
            json.dump({'data': section.m_to_dict(with_root_def=True)}, fp)

        # Tell NOMAD the file was added so it gets parsed immediately
        parent_archive.m_context.process_updated_raw_file(file_name)

    # Nice to have: a reference you could store on the parent entry
    return get_reference(
        parent_archive.metadata.upload_id,
        get_entry_id_from_file_name(file_name, parent_archive),
    )