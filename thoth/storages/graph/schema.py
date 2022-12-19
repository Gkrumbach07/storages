import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField

from .models import PythonPackageVersion as PythonPackageVersionModel
from .models import PythonPackageVersionEntity as PythonPackageVersionEntityModel
from .models import DependsOn as DependsOnModel

from .models import Solved as SolvedModel


class PythonPackageVersion(SQLAlchemyObjectType):
    class Meta:
        model = PythonPackageVersionModel
        interfaces = (relay.Node, )

class PythonPackageVersionEntity(SQLAlchemyObjectType):
    class Meta:
        model = PythonPackageVersionEntityModel
        interfaces = (relay.Node, )

class DependsOn(SQLAlchemyObjectType):
    class Meta:
        model = DependsOnModel
        interfaces = (relay.Node, )


class Solved(SQLAlchemyObjectType):
    class Meta:
        model = SolvedModel
        interfaces = (relay.Node, )
    
class Query(graphene.ObjectType):
    node = relay.Node.Field()
    all_python_package_version = SQLAlchemyConnectionField(PythonPackageVersion.connection)
    all_solved = SQLAlchemyConnectionField(Solved.connection)
    search = graphene.List(PythonPackageVersion, q=graphene.String())

    def resolve_search(self, info, **args):
        q = args.get("q")  # Search query
    
        # Get query
        query = PythonPackageVersion.get_query(info)

        # Query
        pythonPackageVersions = query.filter(PythonPackageVersionModel.package_name.contains(q)).all()

        return pythonPackageVersions



schema = graphene.Schema(query=Query)