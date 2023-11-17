from fastapi import Query

from typing import Annotated

from netbox_proxbox.backend.session.netbox import NetboxSessionDep
from netbox_proxbox.backend.exception import ProxboxException

from netbox_proxbox.backend.schemas.netbox.virtualization import ClusterTypeSchema


class NetboxBase:
    """
    Class to handle Netbox 'Objects'.
    
    Logic: 
        1. it will use 'id' to get the 'Objects' from Netbox if provided.
            1.1. if object is returned, it will return it.
            1.2. if object is not returned, it will raise an `ProxboxException`.
        2. if 'site_id' is not provided, it will check if there's any Site registered on Netbox.
            2.1. if there's no 'Objects' registered on Netbox, it will create a default one.
            2.2. if there's any 'Objects' registered on Netbox, it will check if is Proxbox one by checking tag and name.
                2.2.1. if it's Proxbox one, it will return it.
                2.2.2. if it's not Proxbox one, it will create a default one.
        3. if 'all' is True, it will return all 'Objects' registered on Netbox.
    """

    def __init__(
        self,
        nb: NetboxSessionDep,
        id: Annotated[
            int,
            Query(
                title="Cluster Type ID", description="Netbox Cluster Type ID of Nodes and/or Clusters."
            )
        ] = None,
        all: Annotated[
            bool,
            Query(title="List All Cluster Types", description="List all Cluster Types registered on Netbox.")
        ] = False,
        
    ):
        self.nb = nb
        self.id = id
        self.all = all
        self.pynetbox_path = getattr(getattr(self.nb.session, self.app), self.endpoint)
        
    # Default Cluster Type Params
    default_name = None
    default_slug = None
    default_description = None
    
    # Parameters to be used as Pynetbox class attributes
    app = None
    endpoint = None
    

    
    
    async def get(self):
        # 1. If 'id' provided, use it to get the Cluster Type from Netbox using it.
        if self.id:
            response = None
            
            try:
                response = self.pynetbox_path.get(self.id)
            
            except Exception as error:
                raise ProxboxException(
                    message="Error trying to get Cluster Type from Netbox using the specified ID '{self.id}'.",
                    error=f"{error}"
                )
            
            # 1.1. Return found object.
            if response != None:
                return response
            
            # 1.2. Raise ProxboxException if object is not found.
            else:
                raise ProxboxException(
                    message=f"Cluster Type with ID '{self.id}' not found on Netbox."
                )
        
        # 2. Check if there's any Cluster Type registered on Netbox.
        else:
            try:
                response = self.pynetbox_path.all()
                
                # 2.1. If there's no Cluster Type registered on Netbox, create a default one.
                if len(response) == 0:
                    default_cluster_type_obj = await self.post(default=True)
                    
                    return default_cluster_type_obj
                
                else:
                    # 3. If Query param 'all' is True, return all Cluster Types registered.
                    if self.all:
                        response_list = []
                        
                        for cluster_type in response:
                            response_list.append(cluster_type)
                        
                        return response_list
                    
                    # 2.2
                    # 2.2.1 If there's any Cluster Type registered on Netbox, check if is Proxbox one by checking tag and name.
                    get_proxbox_cluster_type = self.pynetbox_path.get(
                        name=self.default_name,
                        slug=self.default_slug,
                        tags=[self.nb.tag.id]
                    )

                    if get_proxbox_cluster_type != None:
                        return get_proxbox_cluster_type
                    
                    # 2.2.2. If it's not Proxbox one, create a default one.
                    default_cluster_type_obj = await self.post(default=True)
                    return default_cluster_type_obj
                
            except Exception as error:
                raise ProxboxException(
                    message="Error trying to get 'Cluster Types' from Netbox.",
                    python_exception=f"{error}"
                )
                
    async def post(self, default: bool = False, data: ClusterTypeSchema = None):
        if default:
            try:
                response = self.pynetbox_path.create(
                    name = self.default_name,
                    slug = self.default_slug,
                    description = self.default_description,
                    tags = [self.nb.tag.id]
                )
                
                return response
            
            except Exception as error:
                raise ProxboxException(
                    message="Error trying to create default Cluster Type on Netbox.",
                    python_exception=f"{error}"
                )
        
        if data:
            try:
                data_dict = data.model_dump(exclude_unset=True)
                
                response = self.pynetbox_path.create(data_dict)
                return response
            
            except Exception as error:
                raise ProxboxException(
                    message="Error trying to create Cluster Type on Netbox.",
                    detail=f"Payload provided: {data_dict}",
                    python_exception=f"{error}"
                )
